import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowUpRight,
  Bath,
  BedDouble,
  Building2,
  Check,
  ChevronDown,
  Edit3,
  Filter,
  MapPin,
  Plus,
  Ruler,
  Search,
  Trash2,
} from 'lucide-react';

import {
  catalogsApi,
  propertiesApi,
  rentalsApi,
} from '../../api/services';

import { getApiError } from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import { money } from '../../lib/format';

import type {
  Barrio,
  Caracteristica,
  Propiedad,
  TipoPropiedad,
} from '../../types';

import {
  Alert,
  Button,
  EmptyState,
  Field,
  LoadingState,
  Modal,
  PageHeader,
  StatusBadge,
} from '../../components/ui';

type PropertyForm = {
  titulo: string;
  descripcion: string;
  precio_mensual: string;
  direccion: string;
  estrato: string;
  area_m2: string;
  habitaciones: string;
  banos: string;
  tipo: TipoPropiedad;
  barrio_id: string;
};

const blankForm: PropertyForm = {
  titulo: '',
  descripcion: '',
  precio_mensual: '',
  direccion: '',
  estrato: '4',
  area_m2: '',
  habitaciones: '2',
  banos: '1',
  tipo: 'apartamento',
  barrio_id: '',
};

export default function PropiedadesList() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);

  const isOwner = user?.rol === 'propietario';
  const isTenant = user?.rol === 'arrendatario';
  const isAdmin = user?.rol === 'admin';

  const [items, setItems] = useState<Propiedad[]>([]);
  const [barrios, setBarrios] = useState<Barrio[]>([]);
  const [features, setFeatures] = useState<Caracteristica[]>([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('todos');
  const [typeFilter, setTypeFilter] = useState('todos');

  const [modal, setModal] = useState<'edit' | 'request' | 'detail' | null>(null);

  const [detailLoading, setDetailLoading] = useState(false);
  const [selected, setSelected] = useState<Propiedad | null>(null);

  const [form, setForm] = useState<PropertyForm>(blankForm);
  const [selectedFeatures, setSelectedFeatures] = useState<number[]>([]);

  const [requestMessage, setRequestMessage] = useState('');

  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);

  useEffect(() => {
    const urls = selectedImages.map((file) => URL.createObjectURL(file));

    setImagePreviews(urls);

    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [selectedImages]);

  async function loadData() {
    setLoading(true);
    setError('');

    try {
      const [properties, neighborhoods, amenities] = await Promise.all([
        isOwner ? propertiesApi.mine() : propertiesApi.listPublic({}),
        catalogsApi.neighborhoods(),
        catalogsApi.features(),
      ]);

      setItems(properties);
      setBarrios(neighborhoods);
      setFeatures(amenities);
    } catch (err) {
      setError(
        getApiError(err, 'No fue posible cargar las propiedades.')
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    // El rol determina qué inventario se consulta.
  }, [user?.rol]);

  const filtered = useMemo(
    () =>
      items.filter((item) => {
        const normalized = search.trim().toLowerCase();

        const matchesSearch =
          !normalized ||
          [
            item.titulo,
            item.direccion,
            item.barrio?.nombre,
            item.descripcion,
          ].some((value) =>
            value?.toLowerCase().includes(normalized)
          );

        const matchesStatus =
          statusFilter === 'todos' || item.estado === statusFilter;

        const matchesType =
          typeFilter === 'todos' || item.tipo === typeFilter;

        return (
          matchesSearch &&
          matchesStatus &&
          matchesType &&
          (!isTenant || item.estado === 'disponible')
        );
      }),
    [items, search, statusFilter, typeFilter, isTenant]
  );

  const updateForm = (key: keyof PropertyForm, value: string) => {
    setForm((current) => ({
      ...current,
      [key]: value,
    }));
  };

  function openCreate() {
    navigate('/asistente-ia?modo=registro');
  }

  async function openDetails(property: Propiedad) {
    setSelected(property);
    setError('');
    setModal('detail');
    setDetailLoading(true);

    try {
      setSelected(await propertiesApi.get(property.id));
    } catch (err) {
      setError(
        getApiError(
          err,
          'No fue posible consultar el detalle del inmueble.'
        )
      );
    } finally {
      setDetailLoading(false);
    }
  }

  const openEdit = (property: Propiedad) => {
    setSelected(property);
    setSelectedImages([]);

    setForm({
      titulo: property.titulo,
      descripcion: property.descripcion || '',
      precio_mensual: String(property.precio_mensual),
      direccion: property.direccion,
      estrato: String(property.estrato),
      area_m2: property.area_m2 ? String(property.area_m2) : '',
      habitaciones: String(property.habitaciones),
      banos: String(property.banos),
      tipo: property.tipo,
      barrio_id: property.barrio_id
        ? String(property.barrio_id)
        : '',
    });

    setSelectedFeatures(
      property.caracteristicas.map((feature) => feature.id)
    );

    setError('');
    setModal('edit');
  };

  // La edición conserva el formulario tradicional.
  async function saveProperty(event: FormEvent) {
    event.preventDefault();

    if (!selected) return;

    setSaving(true);
    setError('');
    setSuccess('');

    const payload: Record<string, unknown> = {
      titulo: form.titulo.trim(),
      descripcion: form.descripcion.trim() || null,
      precio_mensual: Number(form.precio_mensual),
      direccion: form.direccion.trim(),
      estrato: Number(form.estrato),
      area_m2: form.area_m2 ? Number(form.area_m2) : null,
      habitaciones: Number(form.habitaciones),
      banos: Number(form.banos),
      tipo: form.tipo,
      barrio_id: form.barrio_id
        ? Number(form.barrio_id)
        : null,
    };

    try {
      payload.estado = selected.estado;

      await propertiesApi.update(selected.id, payload);

      await propertiesApi.updateFeatures(
        selected.id,
        selectedFeatures
      );

      if (selectedImages.length) {
        await propertiesApi.uploadImages(
          selected.id,
          selectedImages
        );
      }

      setModal(null);
      setSuccess('Los cambios de la propiedad fueron guardados.');

      await loadData();
    } catch (err) {
      setError(
        getApiError(err, 'No fue posible guardar los cambios.')
      );
    } finally {
      setSaving(false);
    }
  }

  function selectPropertyImages(files: FileList | null) {
    if (!files) return;

    const incoming = Array.from(files);
    const existingCount =
      modal === 'edit' ? selected?.imagenes.length || 0 : 0;

    if (
      existingCount + selectedImages.length + incoming.length >
      10
    ) {
      setError('Puedes guardar máximo 10 fotos por propiedad.');
      return;
    }

    const invalid = incoming.find(
      (file) =>
        !['image/jpeg', 'image/png', 'image/webp'].includes(
          file.type
        ) || file.size > 5 * 1024 * 1024
    );

    if (invalid) {
      setError(
        'Usa imágenes JPG, PNG o WEBP de máximo 5 MB cada una.'
      );
      return;
    }

    setError('');

    setSelectedImages((current) => [
      ...current,
      ...incoming,
    ]);
  }

  async function deleteProperty(property: Propiedad) {
    if (
      !window.confirm(
        `¿Seguro que deseas eliminar "${property.titulo}"? Esta acción no se puede deshacer.`
      )
    ) {
      return;
    }

    setError('');
    setSuccess('');

    try {
      await propertiesApi.remove(property.id);

      setSuccess('La propiedad fue eliminada.');

      await loadData();
    } catch (err) {
      setError(
        getApiError(err, 'No fue posible eliminar la propiedad.')
      );
    }
  }

  async function sendRequest(event: FormEvent) {
    event.preventDefault();

    if (!selected) return;

    setSaving(true);
    setError('');

    try {
      await rentalsApi.request(
        selected.id,
        requestMessage.trim() || undefined
      );

      setModal(null);
      setRequestMessage('');

      setSuccess(
        'Tu solicitud de arriendo fue enviada. Puedes seguir su estado en Arriendos.'
      );
    } catch (err) {
      setError(
        getApiError(err, 'No fue posible enviar la solicitud.')
      );
    } finally {
      setSaving(false);
    }
  }

  const title = isOwner
    ? 'Mis propiedades'
    : isTenant
      ? 'Encuentra tu próximo lugar'
      : 'Inventario de propiedades';

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow={
          isTenant
            ? 'EXPLORAR INMUEBLES'
            : 'GESTIÓN INMOBILIARIA'
        }
        title={title}
        description={
          isOwner
            ? 'Administra tus inmuebles, actualiza sus datos y mantén tu inventario al día.'
            : isTenant
              ? 'Explora opciones disponibles en Medellín y envía solicitudes directamente desde RENTIO.'
              : 'Consulta el inventario publicado y revisa el estado de cada inmueble.'
        }
        action={
          isOwner ? (
            <Button onClick={openCreate}>
              <Plus size={17} /> Nueva propiedad
            </Button>
          ) : undefined
        }
      />

      {error && modal === null && <Alert>{error}</Alert>}

      {success && (
        <Alert
          variant="success"
          onClose={() => setSuccess('')}
        >
          {success}
        </Alert>
      )}

      <div className="property-toolbar">
        <div className="search-box">
          <Search size={18} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Buscar por título, dirección o barrio..."
          />
        </div>

        <div className="toolbar-filters">
          {!isTenant && (
            <label className="select-wrap">
              <Filter size={16} />
              <select
                value={statusFilter}
                onChange={(event) =>
                  setStatusFilter(event.target.value)
                }
              >
                <option value="todos">Todos los estados</option>
                <option value="disponible">Disponible</option>
                <option value="arrendada">Arrendada</option>
                <option value="inactiva">Inactiva</option>
              </select>
              <ChevronDown size={14} />
            </label>
          )}

          <label className="select-wrap">
            <select
              value={typeFilter}
              onChange={(event) =>
                setTypeFilter(event.target.value)
              }
            >
              <option value="todos">Todos los tipos</option>
              <option value="apartamento">Apartamento</option>
              <option value="casa">Casa</option>
              <option value="habitacion">Habitación</option>
              <option value="finca">Finca</option>
            </select>
            <ChevronDown size={14} />
          </label>
        </div>
      </div>

      <div className="list-meta">
        <span>
          <strong>{filtered.length}</strong>{' '}
          {filtered.length === 1 ? 'resultado' : 'resultados'}
        </span>
        <span>
          {isTenant
            ? 'Solo inmuebles disponibles'
            : 'Información consultada desde RENTIO'}
        </span>
      </div>

      {loading ? (
        <LoadingState label="Cargando inventario..." />
      ) : filtered.length === 0 ? (
        <EmptyState
          title="No encontramos propiedades"
          description={
            search ||
            statusFilter !== 'todos' ||
            typeFilter !== 'todos'
              ? 'Prueba cambiando los filtros de búsqueda.'
              : isOwner
                ? 'Todavía no has registrado inmuebles. Crea tu primera propiedad para empezar.'
                : 'En este momento no hay inmuebles que coincidan con esta consulta.'
          }
          action={
            isOwner ? (
              <Button onClick={openCreate}>
                <Plus size={16} /> Registrar propiedad
              </Button>
            ) : undefined
          }
        />
      ) : (
        <div className="property-grid">
          {filtered.map((property, index) => (
            <article className="property-card" key={property.id}>
              <div
                className={`property-visual property-visual-${index % 4}`}
              >
                {property.imagenes?.[0]?.url && (
                  <img
                    className="property-cover-image"
                    src={property.imagenes[0].url}
                    alt={`Fotografía de ${property.titulo}`}
                    loading="lazy"
                    onError={(event) => {
                      event.currentTarget.style.display = 'none';
                    }}
                  />
                )}

                <div className="property-visual-top">
                  <span className="property-type-pill">
                    {property.tipo}
                  </span>
                  <StatusBadge value={property.estado} />
                </div>

                <Building2 size={48} strokeWidth={1.1} />

                <span className="property-visual-caption">
                  RENTIO · MEDELLÍN
                </span>
              </div>

              <div className="property-card-body">
                <div className="property-location">
                  <MapPin size={14} />
                  {property.barrio?.nombre || property.direccion}
                </div>

                <h3>{property.titulo}</h3>

                <p className="property-address">
                  {property.direccion}
                </p>

                <button
                  className="property-detail-link"
                  type="button"
                  onClick={() => openDetails(property)}
                >
                  Ver detalles <ArrowUpRight size={14} />
                </button>

                <div className="property-features">
                  <span>
                    <BedDouble size={15} /> {property.habitaciones} hab.
                  </span>

                  <span>
                    <Bath size={15} /> {property.banos} baños
                  </span>

                  {property.area_m2 && (
                    <span>
                      <Ruler size={15} /> {property.area_m2} m²
                    </span>
                  )}
                </div>

                <div className="property-card-footer">
                  <div>
                    <strong>{money(property.precio_mensual)}</strong>
                    <small>mensuales</small>
                  </div>

                  {isOwner || isAdmin ? (
                    <div className="card-actions">
                      <button
                        className="icon-button"
                        title="Editar"
                        onClick={() => openEdit(property)}
                      >
                        <Edit3 size={16} />
                      </button>

                      <button
                        className="icon-button icon-button-danger"
                        title="Eliminar"
                        onClick={() => deleteProperty(property)}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ) : (
                    <Button
                      size="sm"
                      onClick={() => {
                        setSelected(property);
                        setModal('request');
                        setError('');
                      }}
                    >
                      Me interesa <Plus size={15} />
                    </Button>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {/* EDICIÓN DE PROPIEDAD */}
      {modal === 'edit' && selected && (
        <Modal
          title="Editar propiedad"
          onClose={() => setModal(null)}
          wide
        >
          <form onSubmit={saveProperty} className="modal-form">
            {error && <Alert>{error}</Alert>}

            <div className="form-section-title">
              Información principal
            </div>

            <Field label="Título de la publicación">
              <input
                className="text-input"
                minLength={5}
                maxLength={255}
                required
                value={form.titulo}
                onChange={(event) =>
                  updateForm('titulo', event.target.value)
                }
              />
            </Field>

            <Field label="Descripción">
              <textarea
                className="text-input textarea-input"
                maxLength={5000}
                value={form.descripcion}
                onChange={(event) =>
                  updateForm('descripcion', event.target.value)
                }
                rows={3}
              />
            </Field>

            <div className="form-grid-two">
              <Field label="Precio mensual (COP)">
                <input
                  className="text-input"
                  type="number"
                  min="0"
                  step="1000"
                  required
                  value={form.precio_mensual}
                  onChange={(event) =>
                    updateForm('precio_mensual', event.target.value)
                  }
                />
              </Field>

              <Field label="Dirección">
                <input
                  className="text-input"
                  minLength={5}
                  maxLength={500}
                  required
                  value={form.direccion}
                  onChange={(event) =>
                    updateForm('direccion', event.target.value)
                  }
                />
              </Field>
            </div>

            <div className="form-section-title">
              Fotografías del inmueble
            </div>

            <Field
              label="Selecciona hasta 10 imágenes"
              hint="Formatos JPG, PNG o WEBP. Máximo 5 MB por fotografía."
            >
              <input
                className="text-input"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                multiple
                onChange={(event) => {
                  selectPropertyImages(event.target.files);
                  event.currentTarget.value = '';
                }}
              />
            </Field>

            {selected.imagenes?.length > 0 && (
              <div className="property-photo-preview-grid">
                {selected.imagenes.map((image) => (
                  <div
                    className="property-photo-preview"
                    key={image.id}
                  >
                    <img
                      src={image.url}
                      alt="Fotografía del inmueble"
                    />

                    <button
                      type="button"
                      onClick={async () => {
                        try {
                          const images =
                            await propertiesApi.deleteImage(
                              selected.id,
                              image.id
                            );

                          setSelected({
                            ...selected,
                            imagenes: images,
                          });

                          setItems((current) =>
                            current.map((item) =>
                              item.id === selected.id
                                ? { ...item, imagenes: images }
                                : item
                            )
                          );
                        } catch (err) {
                          setError(
                            getApiError(
                              err,
                              'No fue posible eliminar la fotografía.'
                            )
                          );
                        }
                      }}
                    >
                      Quitar
                    </button>
                  </div>
                ))}
              </div>
            )}

            {imagePreviews.length > 0 && (
              <div className="property-photo-preview-grid">
                {imagePreviews.map((url, index) => (
                  <div className="property-photo-preview" key={url}>
                    <img
                      src={url}
                      alt={selectedImages[index]?.name || 'Nueva fotografía'}
                    />

                    <button
                      type="button"
                      onClick={() =>
                        setSelectedImages((current) =>
                          current.filter((_, i) => i !== index)
                        )
                      }
                    >
                      Quitar
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="form-section-title">
              Características del inmueble
            </div>

            <div className="form-grid-three">
              <Field label="Tipo">
                <select
                  className="text-input"
                  value={form.tipo}
                  onChange={(event) =>
                    updateForm('tipo', event.target.value)
                  }
                >
                  <option value="apartamento">Apartamento</option>
                  <option value="casa">Casa</option>
                  <option value="habitacion">Habitación</option>
                  <option value="finca">Finca</option>
                </select>
              </Field>

              <Field label="Estrato">
                <select
                  className="text-input"
                  value={form.estrato}
                  onChange={(event) =>
                    updateForm('estrato', event.target.value)
                  }
                >
                  {[1, 2, 3, 4, 5, 6].map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="Barrio">
                <select
                  className="text-input"
                  value={form.barrio_id}
                  onChange={(event) =>
                    updateForm('barrio_id', event.target.value)
                  }
                >
                  <option value="">Sin especificar</option>

                  {barrios.map((barrio) => (
                    <option key={barrio.id} value={barrio.id}>
                      {barrio.nombre} · {barrio.comuna}
                    </option>
                  ))}
                </select>
              </Field>
            </div>

            <div className="form-grid-three">
              <Field label="Habitaciones">
                <input
                  className="text-input"
                  type="number"
                  min="0"
                  max="50"
                  value={form.habitaciones}
                  onChange={(event) =>
                    updateForm('habitaciones', event.target.value)
                  }
                />
              </Field>

              <Field label="Baños">
                <input
                  className="text-input"
                  type="number"
                  min="0"
                  max="50"
                  value={form.banos}
                  onChange={(event) =>
                    updateForm('banos', event.target.value)
                  }
                />
              </Field>

              <Field label="Área (m²)">
                <input
                  className="text-input"
                  type="number"
                  min="1"
                  step="0.1"
                  value={form.area_m2}
                  onChange={(event) =>
                    updateForm('area_m2', event.target.value)
                  }
                  placeholder="Opcional"
                />
              </Field>
            </div>

            <div className="form-field">
              <span className="field-label">
                Características adicionales
              </span>

              <div className="feature-picker">
                {features.length ? (
                  features.map((feature) => (
                    <button
                      type="button"
                      key={feature.id}
                      onClick={() =>
                        setSelectedFeatures((current) =>
                          current.includes(feature.id)
                            ? current.filter(
                                (id) => id !== feature.id
                              )
                            : [...current, feature.id]
                        )
                      }
                      className={`feature-chip ${
                        selectedFeatures.includes(feature.id)
                          ? 'feature-chip-active'
                          : ''
                      }`}
                    >
                      {selectedFeatures.includes(feature.id) ? (
                        <Check size={14} />
                      ) : (
                        <Plus size={14} />
                      )}

                      {feature.nombre}
                    </button>
                  ))
                ) : (
                  <span className="field-hint">
                    No hay características registradas en el catálogo.
                  </span>
                )}
              </div>
            </div>

            <Field label="Estado de publicación">
              <select
                className="text-input"
                value={selected.estado}
                onChange={(event) =>
                  setSelected({
                    ...selected,
                    estado: event.target.value as Propiedad['estado'],
                  })
                }
              >
                <option value="disponible">Disponible</option>
                <option value="arrendada">Arrendada</option>
                <option value="inactiva">Inactiva</option>
              </select>

              <span className="field-hint">
                El cambio de estado se guarda junto con los demás datos.
              </span>
            </Field>

            <div className="modal-actions">
              <Button
                type="button"
                variant="secondary"
                onClick={() => setModal(null)}
              >
                Cancelar
              </Button>

              <Button type="submit" disabled={saving}>
                {saving ? 'Guardando...' : 'Guardar cambios'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* DETALLE DE PROPIEDAD */}
      {modal === 'detail' && selected && (
        <Modal
          title="Detalle del inmueble"
          onClose={() => setModal(null)}
          wide
        >
          <div className="property-detail-modal">
            {detailLoading && (
              <LoadingState label="Consultando detalle actualizado..." />
            )}

            {error && <Alert>{error}</Alert>}

            <div className="property-detail-heading">
              <div>
                <span className="eyebrow">
                  {selected.barrio?.nombre || 'MEDELLÍN'}
                </span>

                <h3>{selected.titulo}</h3>
                <p>{selected.direccion}</p>
              </div>

              <StatusBadge value={selected.estado} />
            </div>

            <div className="property-detail-price">
              {money(selected.precio_mensual)}{' '}
              <small>canon mensual</small>
            </div>

            {selected.imagenes?.length > 0 && (
              <div className="property-detail-gallery">
                {selected.imagenes.map((image) => (
                  <img
                    key={image.id}
                    src={image.url}
                    alt={`Fotografía de ${selected.titulo}`}
                    loading="lazy"
                  />
                ))}
              </div>
            )}

            {selected.descripcion && (
              <p className="property-detail-description">
                {selected.descripcion}
              </p>
            )}

            <div className="property-detail-specs">
              <div>
                <BedDouble size={17} />
                <strong>{selected.habitaciones}</strong>
                <span>Habitaciones</span>
              </div>

              <div>
                <Bath size={17} />
                <strong>{selected.banos}</strong>
                <span>Baños</span>
              </div>

              <div>
                <Ruler size={17} />
                <strong>
                  {selected.area_m2
                    ? `${selected.area_m2} m²`
                    : 'No reportada'}
                </strong>
                <span>Área</span>
              </div>

              <div>
                <Building2 size={17} />
                <strong>{selected.estrato}</strong>
                <span>Estrato</span>
              </div>
            </div>

            <div className="property-detail-meta">
              <span>
                Tipo: <strong>{selected.tipo}</strong>
              </span>

              <span>
                Comuna:{' '}
                <strong>
                  {selected.barrio?.comuna || 'No especificada'}
                </strong>
              </span>

              <span>
                Zona:{' '}
                <strong>
                  {selected.barrio?.zona || 'No especificada'}
                </strong>
              </span>
            </div>

            <div className="property-detail-features">
              <span className="field-label">Características</span>

              {selected.caracteristicas?.length ? (
                <div className="feature-cloud">
                  {selected.caracteristicas.map((feature) => (
                    <span className="feature-chip" key={feature.id}>
                      {feature.nombre}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="muted-inline">
                  No se han registrado características adicionales.
                </p>
              )}
            </div>

            <div className="modal-actions">
              <Button
                type="button"
                variant="secondary"
                onClick={() => setModal(null)}
              >
                Cerrar
              </Button>

              {isTenant && selected.estado === 'disponible' && (
                <Button
                  type="button"
                  onClick={() => {
                    setRequestMessage('');
                    setError('');
                    setModal('request');
                  }}
                >
                  Enviar solicitud <ArrowUpRight size={15} />
                </Button>
              )}

              {(isOwner || isAdmin) && (
                <Button
                  type="button"
                  onClick={() => openEdit(selected)}
                >
                  Editar inmueble <Edit3 size={15} />
                </Button>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* SOLICITUD DE ARRIENDO */}
      {modal === 'request' && selected && (
        <Modal
          title="Enviar solicitud de arriendo"
          onClose={() => setModal(null)}
        >
          <form className="modal-form" onSubmit={sendRequest}>
            {error && <Alert>{error}</Alert>}

            <div className="request-property-summary">
              <strong>{selected.titulo}</strong>
              <span>
                {selected.barrio?.nombre || selected.direccion}
              </span>
              <b>
                {money(selected.precio_mensual)} <small>/ mes</small>
              </b>
            </div>

            <Field
              label="Mensaje para el propietario"
              hint="Cuéntale brevemente por qué te interesa el inmueble. (Opcional)"
            >
              <textarea
                className="text-input textarea-input"
                rows={4}
                maxLength={1000}
                value={requestMessage}
                onChange={(event) =>
                  setRequestMessage(event.target.value)
                }
                placeholder="Hola, estoy interesado en conocer más sobre esta propiedad..."
              />
            </Field>

            <div className="modal-actions">
              <Button
                type="button"
                variant="secondary"
                onClick={() => setModal(null)}
              >
                Cancelar
              </Button>

              <Button type="submit" disabled={saving}>
                {saving ? 'Enviando...' : 'Enviar solicitud'}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}