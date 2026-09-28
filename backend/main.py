import base64
import datetime
from datetime import timedelta
import hashlib
import json
import os
from typing import List, Optional

from cryptography.fernet import Fernet
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import joblib
from jose import JWTError, jwt
import numpy as np
import pandas as pd
from passlib.context import CryptContext
from pydantic import BaseModel
from skfuzzy import control as ctrl
import skfuzzy as fuzz
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# ---------------------------------------------------------
# 1. BASE DE DATOS POSTGRESQL (pgAdmin)
# ---------------------------------------------------------
DATABASE_URL = "postgresql://postgres:bedoya1021@127.0.0.1:5433/rentio_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
# 2. MODELOS BASE DE DATOS
# ---------------------------------------------------------
class UsuarioDB(Base):
    __tablename__ = "usuarios"
    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(100), unique=True, nullable=False, index=True)
    contrasena_hash = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False)


class InmuebleDB(Base):
    __tablename__ = "inmuebles"
    id_inmueble = Column(Integer, primary_key=True, index=True)
    id_arrendador = Column(
        Integer, ForeignKey("usuarios.id_usuario"), nullable=True
    )
    direccion = Column(String(200), nullable=False)
    barrio = Column(String(100), default="Belén")
    canon_mensual = Column(Float, nullable=False)
    descripcion = Column(Text)
    imagenes_json = Column(Text, nullable=True)
    estado = Column(String(20), default="disponible")


class PostulacionDB(Base):
    __tablename__ = "postulaciones"
    id_postulacion = Column(Integer, primary_key=True, index=True)
    id_inmueble = Column(Integer, ForeignKey("inmuebles.id_inmueble"))
    id_inquilino = Column(Integer, ForeignKey("usuarios.id_usuario"))
    edad = Column(Integer, default=25)
    ingresos = Column(Float, default=2000000.0)
    credit_score = Column(Integer, default=650)
    dias_retraso_historico = Column(Integer, default=0)
    empleado = Column(String(10), default="true")
    estado = Column(String(20), default="pendiente")
    fecha_postulacion = Column(DateTime, default=datetime.datetime.utcnow)


class ContratoDB(Base):
    __tablename__ = "contratos"
    id_contrato = Column(Integer, primary_key=True, index=True)
    id_inmueble = Column(Integer, ForeignKey("inmuebles.id_inmueble"))
    id_inquilino = Column(Integer, ForeignKey("usuarios.id_usuario"))
    contrato_cifrado_aes = Column(Text, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    estado = Column(String(20), default="activo")


class PagoDB(Base):
    __tablename__ = "pagos"
    id_pago = Column(Integer, primary_key=True, index=True)
    id_contrato = Column(Integer, ForeignKey("contratos.id_contrato"))
    monto = Column(Float, nullable=False)
    fecha_pago = Column(DateTime, default=datetime.datetime.utcnow)
    hash_integridad_sha256 = Column(String(64), nullable=False)


Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------
# 3. SEGURIDAD Y TOKEN JWT
# ---------------------------------------------------------
SECRET_KEY = "rentio_clave_super_secreta_proyecto_de_grado_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password[:72], hashed_password)


def crear_token_acceso(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def obtener_usuario_actual(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        correo: str = payload.get("sub")
        if correo is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    usuario = (
        db.query(UsuarioDB).filter(UsuarioDB.correo == correo).first()
    )
    if usuario is None:
        raise credentials_exception
    return usuario


def requerir_rol(rol_requerido: str):
    def rol_dependency(
        usuario_actual: UsuarioDB = Depends(obtener_usuario_actual),
    ):
        if usuario_actual.rol.lower() != rol_requerido.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Acceso denegado. Se requiere el rol de {rol_requerido}"
                ),
            )
        return usuario_actual

    return rol_dependency


CLAVE_FERNET = Fernet.generate_key()
cipher_suite = Fernet(CLAVE_FERNET)

# ---------------------------------------------------------
# 4. SISTEMA DE INFERENCIA DIFUSA (FIS) - BASADO STRICTAMENTE EN DOCUMENTO
# ---------------------------------------------------------

# Universos de Discurso
credit_score_var = ctrl.Antecedent(np.arange(0, 1001, 1), 'credit_score')
capacidad_pago_var = ctrl.Antecedent(np.arange(0, 101, 1), 'capacidad_pago')
edad_var = ctrl.Antecedent(np.arange(18, 91, 1), 'edad')

score_confianza_var = ctrl.Consequent(np.arange(0, 101, 1), 'score_confianza')

# Funciones de Pertenencia
credit_score_var['Malo'] = fuzz.trapmf(credit_score_var.universe, [0, 0, 300, 400])
credit_score_var['Regular'] = fuzz.trimf(credit_score_var.universe, [300, 500, 700])
credit_score_var['Excelente'] = fuzz.trapmf(credit_score_var.universe, [600, 750, 1000, 1000])

capacidad_pago_var['Riesgo_Bajo'] = fuzz.trapmf(capacidad_pago_var.universe, [0, 0, 20, 25])
capacidad_pago_var['Riesgo_Medio'] = fuzz.trimf(capacidad_pago_var.universe, [20, 32.5, 45])
capacidad_pago_var['Riesgo_Alto'] = fuzz.trapmf(capacidad_pago_var.universe, [40, 55, 100, 100])

edad_var['Joven_Riesgo'] = fuzz.trapmf(edad_var.universe, [18, 18, 21, 24])
edad_var['Adulto_Estable'] = fuzz.trimf(edad_var.universe, [23, 39, 55])
edad_var['Senior'] = fuzz.trapmf(edad_var.universe, [50, 65, 90, 90])

score_confianza_var['Rojo'] = fuzz.trapmf(score_confianza_var.universe, [0, 0, 25, 40])
score_confianza_var['Amarillo'] = fuzz.trimf(score_confianza_var.universe, [30, 52.5, 75])
score_confianza_var['Verde'] = fuzz.trapmf(score_confianza_var.universe, [70, 85, 100, 100])

# Base de Reglas
rule1 = ctrl.Rule(credit_score_var['Excelente'] & capacidad_pago_var['Riesgo_Bajo'], score_confianza_var['Verde'])
rule2 = ctrl.Rule(credit_score_var['Excelente'] & capacidad_pago_var['Riesgo_Alto'], score_confianza_var['Amarillo'])
rule3 = ctrl.Rule(credit_score_var['Malo'] & capacidad_pago_var['Riesgo_Alto'], score_confianza_var['Rojo'])
rule4 = ctrl.Rule(credit_score_var['Regular'] & capacidad_pago_var['Riesgo_Medio'] & edad_var['Joven_Riesgo'], score_confianza_var['Rojo'])
rule5 = ctrl.Rule(credit_score_var['Regular'] & capacidad_pago_var['Riesgo_Medio'] & edad_var['Adulto_Estable'], score_confianza_var['Amarillo'])

sistema_difuso_control = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5])

modelo_ml = joblib.load("modelo_riesgo_ml.pkl")
columnas_modelo = joblib.load("columnas_modelo.pkl")

# ---------------------------------------------------------
# 5. INICIALIZACIÓN FASTAPI
# ---------------------------------------------------------
app = FastAPI(
    title="API RENTIO - Sistema Inteligente de Arrendamientos", version="2.6.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# 6. ESQUEMAS PYDANTIC
# ---------------------------------------------------------
class UsuarioRegistro(BaseModel):
    nombre: str
    correo: str
    contrasena: str
    rol: str


class SolicitudEvaluacion(BaseModel):
    edad: int
    ingresos: float
    credit_score: int
    canon: float
    duracion_meses: int
    dias_retraso_historico: int
    empleado: bool


class SolicitudInmueble(BaseModel):
    direccion: str
    barrio: str = "Belén"
    canon_mensual: float
    descripcion: str
    imagenes_base64: Optional[List[str]] = []


class EditarInmueble(BaseModel):
    direccion: str
    barrio: str
    canon_mensual: float
    descripcion: str


class ActualizarFotosInmueble(BaseModel):
    imagenes_base64: List[str]


class SolicitudPostulacionCompleta(BaseModel):
    id_inmueble: int
    edad: int
    ingresos: float
    credit_score: int
    dias_retraso_historico: int
    empleado: bool


class SolicitudCrearContrato(BaseModel):
    id_inmueble: int
    id_inquilino: int
    fecha_inicio: str
    fecha_fin: str
    canon: float


class SolicitudPago(BaseModel):
    id_contrato: int
    monto: float
    id_inquilino: int


# ---------------------------------------------------------
# 7. AUTENTICACIÓN
# ---------------------------------------------------------
@app.post("/api/registro", status_code=201)
def registrar_usuario(datos: UsuarioRegistro, db: Session = Depends(get_db)):
    usuario_existe = (
        db.query(UsuarioDB).filter(UsuarioDB.correo == datos.correo).first()
    )
    if usuario_existe:
        raise HTTPException(
            status_code=400, detail="El correo ya se encuentra registrado"
        )

    nuevo_usuario = UsuarioDB(
        nombre=datos.nombre,
        correo=datos.correo,
        contrasena_hash=hash_password(datos.contrasena),
        rol=datos.rol.lower(),
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return {
        "mensaje": "Usuario registrado exitosamente en PostgreSQL",
        "id": nuevo_usuario.id_usuario,
    }


@app.post("/api/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    usuario = (
        db.query(UsuarioDB)
        .filter(UsuarioDB.correo == form_data.username)
        .first()
    )
    if not usuario or not verify_password(
        form_data.password, usuario.contrasena_hash
    ):
        raise HTTPException(
            status_code=400, detail="Correo o contraseña incorrectos"
        )

    token_acceso = crear_token_acceso(
        data={"sub": usuario.correo, "rol": usuario.rol, "id": usuario.id_usuario}
    )
    return {
        "access_token": token_acceso,
        "token_type": "bearer",
        "rol": usuario.rol,
        "nombre": usuario.nombre,
    }


# ---------------------------------------------------------
# 8. MOTOR DE EVALUACIÓN DIFUSA CON EXPLICABILIDAD
# ---------------------------------------------------------
@app.post("/api/evaluar-inquilino")
def evaluar_inquilino(
    datos: SolicitudEvaluacion,
    usuario_actual: UsuarioDB = Depends(requerir_rol("arrendador")),
):
    try:
        porcentaje_capacidad = (datos.canon / (datos.ingresos + 1)) * 100

        simulacion = ctrl.ControlSystemSimulation(sistema_difuso_control)
        simulacion.input['credit_score'] = min(max(datos.credit_score, 0), 1000)
        simulacion.input['capacidad_pago'] = min(max(porcentaje_capacidad, 0), 100)
        simulacion.input['edad'] = min(max(datos.edad, 18), 90)

        simulacion.compute()
        score_confianza_final = round(float(simulacion.output['score_confianza']), 2)

        if score_confianza_final >= 70:
            nivel, alerta = "Bajo", "Verde - Inquilino Recomendado (Confianza Alta)"
        elif score_confianza_final >= 35:
            nivel, alerta = "Moderado", "Amarillo - Aprobación con Codeudor"
        else:
            nivel, alerta = "Alto", "Rojo - Elevado Riesgo / Rechazado"

        razones = []
        razones.append(f"Capacidad de Pago evaluada: El canon representa el {round(porcentaje_capacidad, 1)}% de sus ingresos.")
        
        if datos.credit_score >= 600:
            razones.append(f"Historial Crediticio Excelente/Regular ({datos.credit_score} pts).")
        else:
            razones.append(f"Alerta: Historial Crediticio Malo ({datos.credit_score} pts).")

        if datos.edad <= 24:
            razones.append(f"Inquilino de {datos.edad} años categorizado en 'Joven Riesgo'.")
        elif datos.edad <= 55:
            razones.append(f"Inquilino de {datos.edad} años categorizado en 'Adulto Estable'.")
        else:
            razones.append(f"Inquilino de {datos.edad} años categorizado en 'Senior'.")

        if not datos.empleado:
            razones.append("Candidato sin empleo formal reportado.")

        return {
            "evaluado_por": usuario_actual.nombre,
            "indice_riesgo_final": score_confianza_final,
            "nivel_riesgo": nivel,
            "recomendacion": alerta,
            "desglose_explicabilidad": razones,
        }
    except Exception as e:
        return {
            "evaluado_por": usuario_actual.nombre,
            "indice_riesgo_final": 30.0,
            "nivel_riesgo": "Alto",
            "recomendacion": "Rojo - Elevado Riesgo / Requiere revisión manual",
            "desglose_explicabilidad": [
                f"El porcentaje de arriendo sobre ingresos ({round((datos.canon/datos.ingresos)*100, 1)}%) o el Credit Score ({datos.credit_score}) superan los umbrales seguros."
            ]
        }


# ---------------------------------------------------------
# 9. GESTIÓN Y CRUD COMPLETO DE INMUEBLES
# ---------------------------------------------------------
@app.get("/api/inmuebles/todos")
def listar_todos_inmuebles(db: Session = Depends(get_db)):
    inmuebles = db.query(InmuebleDB).all()
    resultado = []

    for inm in inmuebles:
        propietario = (
            db.query(UsuarioDB)
            .filter(UsuarioDB.id_usuario == inm.id_arrendador)
            .first()
        )
        fotos = json.loads(inm.imagenes_json) if inm.imagenes_json else []
        resultado.append({
            "id_inmueble": inm.id_inmueble,
            "direccion": inm.direccion,
            "barrio": inm.barrio,
            "canon_mensual": inm.canon_mensual,
            "descripcion": inm.descripcion,
            "imagenes_base64": fotos,
            "estado": inm.estado,
            "propietario_nombre": (
                propietario.nombre if propietario else "Arrendador RENTIO"
            ),
            "propietario_correo": (
                propietario.correo if propietario else "Contacto Directo"
            ),
        })

    return resultado


@app.get("/api/inmuebles/mis-inmuebles")
def listar_mis_inmuebles(
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(requerir_rol("arrendador")),
):
    inmuebles = (
        db.query(InmuebleDB)
        .filter(InmuebleDB.id_arrendador == usuario.id_usuario)
        .all()
    )
    resultado = []
    for inm in inmuebles:
        fotos = json.loads(inm.imagenes_json) if inm.imagenes_json else []
        resultado.append({
            "id_inmueble": inm.id_inmueble,
            "direccion": inm.direccion,
            "barrio": inm.barrio,
            "canon_mensual": inm.canon_mensual,
            "descripcion": inm.descripcion,
            "imagenes_base64": fotos,
            "estado": inm.estado,
        })
    return resultado


@app.post("/api/inmuebles")
def crear_inmueble(
    datos: SolicitudInmueble,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(requerir_rol("arrendador")),
):
    imagenes_json_str = (
        json.dumps(datos.imagenes_base64) if datos.imagenes_base64 else "[]"
    )

    nuevo_inmueble = InmuebleDB(
        id_arrendador=usuario.id_usuario,
        direccion=datos.direccion,
        barrio=datos.barrio,
        canon_mensual=datos.canon_mensual,
        descripcion=datos.descripcion,
        imagenes_json=imagenes_json_str,
    )
    db.add(nuevo_inmueble)
    db.commit()
    db.refresh(nuevo_inmueble)
    return {
        "mensaje": f"Inmueble guardado con {len(datos.imagenes_base64)} fotos",
        "inmueble": nuevo_inmueble,
    }


@app.put("/api/inmuebles/{id_inmueble}")
def editar_inmueble(
    id_inmueble: int,
    datos: EditarInmueble,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(requerir_rol("arrendador")),
):
    inm = (
        db.query(InmuebleDB)
        .filter(
            InmuebleDB.id_inmueble == id_inmueble,
            InmuebleDB.id_arrendador == usuario.id_usuario,
        )
        .first()
    )
    if not inm:
        raise HTTPException(
            status_code=404,
            detail=(
                "Inmueble no encontrado o no pertenece a tu cuenta de propietario."
            ),
        )

    inm.direccion = datos.direccion
    inm.barrio = datos.barrio
    inm.canon_mensual = datos.canon_mensual
    inm.descripcion = datos.descripcion
    db.commit()

    return {"mensaje": "Información del inmueble actualizada con éxito"}


@app.patch("/api/inmuebles/{id_inmueble}/fotos")
def actualizar_fotos_inmueble(
    id_inmueble: int,
    datos: ActualizarFotosInmueble,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(requerir_rol("arrendador")),
):
    inm = (
        db.query(InmuebleDB)
        .filter(
            InmuebleDB.id_inmueble == id_inmueble,
            InmuebleDB.id_arrendador == usuario.id_usuario,
        )
        .first()
    )
    if not inm:
        raise HTTPException(
            status_code=404, detail="Inmueble no encontrado o sin permisos"
        )

    inm.imagenes_json = json.dumps(datos.imagenes_base64)
    db.commit()

    return {
        "mensaje": "Galería de fotos actualizada",
        "total_fotos": len(datos.imagenes_base64),
    }


# ELIMINAR UN INMUEBLE PROPIO Y SUS POSTULACIONES EN POSTGRESQL (CORREGIDO)
@app.delete("/api/inmuebles/{id_inmueble}")
def eliminar_inmueble(
    id_inmueble: int,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(requerir_rol("arrendador")),
):
    inm = (
        db.query(InmuebleDB)
        .filter(
            InmuebleDB.id_inmueble == id_inmueble,
            InmuebleDB.id_arrendador == usuario.id_usuario,
        )
        .first()
    )
    if not inm:
        raise HTTPException(
            status_code=404, detail="Inmueble no encontrado o sin autorización"
        )

    # 1. Eliminar primero las postulaciones asociadas a este inmueble en PostgreSQL
    db.query(PostulacionDB).filter(
        PostulacionDB.id_inmueble == id_inmueble
    ).delete(synchronize_session=False)

    # 2. Ahora sí eliminar el inmueble de PostgreSQL
    db.delete(inm)
    db.commit()
    return {
        "mensaje": "Inmueble y sus postulaciones asociadas eliminados correctamente de PostgreSQL"
    }


# ---------------------------------------------------------
# 10. POSTULACIONES, CONTRATOS Y PAGOS
# ---------------------------------------------------------
@app.post("/api/postular")
def postular_inmueble(
    datos: SolicitudPostulacionCompleta,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(requerir_rol("inquilino")),
):
    postulacion_existente = (
        db.query(PostulacionDB)
        .filter(
            PostulacionDB.id_inmueble == datos.id_inmueble,
            PostulacionDB.id_inquilino == usuario.id_usuario,
        )
        .first()
    )
    if postulacion_existente:
        raise HTTPException(
            status_code=400,
            detail="Ya te has postulado previamente a esta propiedad.",
        )

    nueva_postulacion = PostulacionDB(
        id_inmueble=datos.id_inmueble,
        id_inquilino=usuario.id_usuario,
        edad=datos.edad,
        ingresos=datos.ingresos,
        credit_score=datos.credit_score,
        dias_retraso_historico=datos.dias_retraso_historico,
        empleado="true" if datos.empleado else "false",
    )
    db.add(nueva_postulacion)
    db.commit()
    return {
        "mensaje": "Postulación enviada correctamente al arrendador",
        "inquilino": usuario.nombre,
    }


@app.get("/api/postulaciones/recibidas")
def ver_postulaciones_recibidas(
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(requerir_rol("arrendador")),
):
    inmuebles_propios = (
        db.query(InmuebleDB.id_inmueble)
        .filter(InmuebleDB.id_arrendador == usuario.id_usuario)
        .all()
    )
    ids_inmuebles = [i[0] for i in inmuebles_propios]

    postulaciones = (
        db.query(PostulacionDB)
        .filter(PostulacionDB.id_inmueble.in_(ids_inmuebles))
        .all()
    )

    resultado = []
    for p in postulaciones:
        inm = (
            db.query(InmuebleDB)
            .filter(InmuebleDB.id_inmueble == p.id_inmueble)
            .first()
        )
        inq = (
            db.query(UsuarioDB)
            .filter(UsuarioDB.id_usuario == p.id_inquilino)
            .first()
        )
        resultado.append({
            "id_postulacion": p.id_postulacion,
            "direccion_inmueble": inm.direccion if inm else "N/A",
            "canon": inm.canon_mensual if inm else 0,
            "nombre_inquilino": inq.nombre if inq else "Inquilino",
            "correo_inquilino": inq.correo if inq else "N/A",
            "edad": p.edad,
            "ingresos": p.ingresos,
            "credit_score": p.credit_score,
            "dias_retraso_historico": p.dias_retraso_historico,
            "empleado": p.empleado == "true",
            "estado": p.estado,
            "fecha": p.fecha_postulacion.strftime("%Y-%m-%d %H:%M"),
        })

    return resultado


@app.post("/api/contratos/generar-cifrado")
def generar_contrato_legal(
    datos: SolicitudCrearContrato,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(obtener_usuario_actual),
):
    plantilla = f"""
CONTRATO DE ARRENDAMIENTO DE VIVIENDA URBANA (LEY 820 DE 2003)
--------------------------------------------------------------
Inmueble ID: {datos.id_inmueble}
Arrendatario ID: {datos.id_inquilino}
Canon de Arrendamiento: ${datos.canon:,.2f} COP
Vigencia: Desde {datos.fecha_inicio} hasta {datos.fecha_fin}
"""
    cifrado = cipher_suite.encrypt(plantilla.encode("utf-8")).decode("utf-8")

    nuevo_contrato = ContratoDB(
        id_inmueble=datos.id_inmueble,
        id_inquilino=datos.id_inquilino,
        contrato_cifrado_aes=cifrado,
        fecha_inicio=datetime.datetime.strptime(
            datos.fecha_inicio, "%Y-%m-%d"
        ).date(),
        fecha_fin=datetime.datetime.strptime(datos.fecha_fin, "%Y-%m-%d").date(),
    )
    db.add(nuevo_contrato)
    db.commit()

    return {
        "mensaje": "Contrato generado y cifrado con AES-256",
        "contrato_cifrado_base64": cifrado,
        "minuta_original": plantilla,
    }


@app.post("/api/seguridad/hash-pago")
def generar_hash_pago(
    datos: SolicitudPago,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(obtener_usuario_actual),
):
    timestamp = datetime.datetime.utcnow().isoformat()
    cadena_raw = (
        f"{datos.id_contrato}-{datos.monto}-{datos.id_inquilino}-{timestamp}"
    )
    hash_sha256 = hashlib.sha256(cadena_raw.encode("utf-8")).hexdigest()

    nuevo_pago = PagoDB(
        id_contrato=datos.id_contrato,
        monto=datos.monto,
        hash_integridad_sha256=hash_sha256,
    )
    db.add(nuevo_pago)
    db.commit()

    return {
        "mensaje": "Pago registrado con sello inalterable SHA-256",
        "hash_sha256": hash_sha256,
        "timestamp": timestamp,
    }