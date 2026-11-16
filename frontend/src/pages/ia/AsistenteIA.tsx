import { useEffect, useRef, useState, type FormEvent } from 'react';
import {
  Bot,
  Check,
  ImagePlus,
  Lightbulb,
  MessageCircle,
  Plus,
  Send,
  Sparkles,
} from 'lucide-react';

import './AsistenteIA.css';
import { getApiError } from '../../api/client';
import { catalogsApi, marketingApi } from '../../api/services';
import { dateLabel, money } from '../../lib/format';
import type {
  Barrio,
  ConversacionMarketing,
} from '../../types';
import {
  Alert,
  Button,
  LoadingState,
  PageHeader,
  Panel,
  StatusBadge,
} from '../../components/ui';

const REQUIRED_FIELDS = [
  'barrio',
  'tipo',
  'habitaciones',
  'banos',
  'direccion',
  'estrato',
  'precio_mensual',
] as const;

const fieldLabels: Record<string, string> = {
  barrio: 'Barrio',
  tipo: 'Tipo de inmueble',
  habitaciones: 'Habitaciones',
  banos: 'Baños',
  direccion: 'Dirección',
  estrato: 'Estrato',
  precio_mensual: 'Canon mensual',
  area_m2: 'Área',
  parqueadero: 'Parqueadero',
};

const normalize = (value: string) =>
  value
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9]+/g, ' ')
    .trim()
    .toLowerCase();

function hasValue(value: unknown) {
  return value !== undefined && value !== null && value !== '';
}

export default function AsistenteIA() {
  const [neighborhoods, setNeighborhoods] = useState<Barrio[]>([]);
  const [conversations, setConversations] = useState<ConversacionMarketing[]>([]);
  const [conversation, setConversation] = useState<ConversacionMarketing | null>(null);
  const [missingFields, setMissingFields] = useState<string[]>([...REQUIRED_FIELDS]);
  const [message, setMessage] = useState('');
  const [manualCanon, setManualCanon] = useState('');
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [chatLoading, setChatLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let active = true;
    async function loadInitial() {
      setLoading(true);
      setError('');
      try {
        const [chats, barrios] = await Promise.all([
          marketingApi.conversations(),
          catalogsApi.neighborhoods(),
        ]);
        if (!active) return;
        setConversations(chats);
        setNeighborhoods(barrios);
      } catch (err) {
        if (active) setError(getApiError(err, 'No fue posible preparar el asistente RENTIO.'));
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadInitial();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const urls = selectedImages.map((file) => URL.createObjectURL(file));
    setImagePreviews(urls);
    return () => urls.forEach((url) => URL.revokeObjectURL(url));
  }, [selectedImages]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [conversation?.mensajes.length, sending]);

  const propertyData = conversation?.datos_recopilados ?? {};
  const lastResult = conversation?.resultados?.[conversation.resultados.length - 1] ?? null;
  const allMessages = conversation?.mensajes ?? [];
  const isNeighborhoodValid = neighborhoods.some(
    (item) => normalize(item.nombre) === normalize(String(propertyData.barrio ?? '')),
  );
  const isRegistrationReady =
    Boolean(conversation) &&
    conversation?.estado === 'lista' &&
    missingFields.length === 0 &&
    REQUIRED_FIELDS.every((field) => hasValue(propertyData[field])) &&
    Number(propertyData.precio_mensual) > 0;

  async function startConversation() {
    setChatLoading(true);
    setError('');
    setSuccess('');
    setMessage('');
    try {
      const created = await marketingApi.createConversation();
      setConversation(created);
      setMissingFields([...REQUIRED_FIELDS]);
      setConversations((items) => [created, ...items.filter((item) => item.id !== created.id)]);
    } catch (err) {
      setError(getApiError(err, 'No fue posible iniciar la conversación.'));
    } finally {
      setChatLoading(false);
    }
  }

  async function selectConversation(id: number) {
    setChatLoading(true);
    setError('');
    try {
      const detail = await marketingApi.conversation(id);
      setConversation(detail);
      setMissingFields(
        REQUIRED_FIELDS.filter((field) => !hasValue(detail.datos_recopilados?.[field])),
      );
    } catch (err) {
      setError(getApiError(err, 'No fue posible abrir la conversación.'));
    } finally {
      setChatLoading(false);
    }
  }

  async function sendTurn(content: string) {
    if (!conversation || !content.trim() || sending || chatLoading) return;
    const submittedContent = content.trim();
    setSending(true);
    setMessage('');
    setError('');
    try {
      const response = await marketingApi.sendMessage(conversation.id, submittedContent);
      const [detail, chats] = await Promise.all([
        marketingApi.conversation(conversation.id),
        marketingApi.conversations(),
      ]);
      setConversation(detail);
      setConversations(chats);
      setMissingFields(response.datos_faltantes);
    } catch (err) {
      setMessage(submittedContent);
      setError(getApiError(err, 'No fue posible enviar el mensaje. Revisa la conexión con el servicio de IA.'));
    } finally {
      setSending(false);
    }
  }

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    await sendTurn(message);
  }

  async function submitManualCanon(event: FormEvent) {
    event.preventDefault();
    const amount = Number(manualCanon);
    if (!Number.isFinite(amount) || amount <= 0) {
      setError('Ingresa un canon mensual mayor que cero.');
      return;
    }
    await sendTurn(`El canon mensual que decido cobrar es $${amount}`);
    setManualCanon('');
  }

  function selectImages(files: FileList | null) {
    if (!files) return;
    const incoming = Array.from(files);
    if (selectedImages.length + incoming.length > 10) {
      setError('Puedes cargar máximo 10 fotografías.');
      return;
    }
    const invalid = incoming.find(
      (file) =>
        !['image/jpeg', 'image/png', 'image/webp'].includes(file.type) ||
        file.size > 5 * 1024 * 1024,
    );
    if (invalid) {
      setError('Usa imágenes JPG, PNG o WEBP de máximo 5 MB cada una.');
      return;
    }
    setError('');
    setSelectedImages((items) => [...items, ...incoming]);
  }

  async function confirmRegistration() {
    if (!conversation || !isRegistrationReady || saving) return;
    const title = `${String(propertyData.tipo).charAt(0).toUpperCase()}${String(propertyData.tipo).slice(1)} en ${String(propertyData.barrio)}`;
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const created = await marketingApi.createPropertyFromConversation(
        conversation.id,
        {
          titulo: title,
          descripcion: lastResult?.descripcion || null,
          precio_mensual: Number(propertyData.precio_mensual),
        },
        selectedImages,
      );
      setSuccess(`“${created.titulo}” quedó registrada con éxito con ${created.imagenes.length} fotografía(s).`);
      setSelectedImages([]);
      setConversation(await marketingApi.conversation(conversation.id));
      const chats = await marketingApi.conversations();
      setConversations(chats);
    } catch (err) {
      setError(getApiError(err, 'No fue posible confirmar el registro. No se guardó la propiedad.'));
    } finally {
      setSaving(false);
    }
  }

  const datosKeys = [
    'barrio',
    'tipo',
    'habitaciones',
    'banos',
    'direccion',
    'estrato',
    'precio_mensual',
    'area_m2',
    'parqueadero',
  ];

  return (
    <div className="page-stack assistant-page">
      <PageHeader
        eyebrow="RENTIO INTELLIGENCE"
        title="Registro de Propiedades con IA"
        description="Describe tu inmueble conversando libremente. La IA recopila los datos, sugiere un canon basado en el mercado de Medellín, redacta una descripción atractiva y te solicita solo la información faltante."
      />

      {error && <Alert>{error}</Alert>}
      {success && <Alert variant="success" onClose={() => setSuccess('')}>{success}</Alert>}

      {loading ? <LoadingState label="Preparando el asistente..." /> : (
        <div className="assistant-layout">
          <Panel className="assistant-chat-panel">
            <div className="chat-header">
              <div className="chat-header-icon"><Bot size={20} /></div>
              <div>
                <h2>Registro conversacional</h2>
                <p>Describe el inmueble con tus palabras; no necesitas formularios extensos.</p>
              </div>
              <span className="chat-secure"><span className="pulse-dot" /> RENTIO AI</span>
            </div>

            <div className="assistant-toolbar">
              <Button
                type="button"
                variant="secondary"
                disabled={chatLoading}
                onClick={() => void startConversation()}
              >
                <Plus size={16} /> Nueva conversación
              </Button>
            </div>

            {!conversation ? (
              <div className="assistant-empty">
                <div className="chat-bot-large"><Bot size={25} /></div>
                <strong>¡Hola! Cuéntame cómo es tu inmueble.</strong>
                <p>
                  Puedes compartir todos los datos en un solo mensaje. Te preguntaré únicamente lo que haga falta y podrás corregir cualquier dato conversando.
                </p>
                <Button onClick={() => void startConversation()} disabled={chatLoading}>
                  <MessageCircle size={16} /> Comenzar registro
                </Button>
              </div>
            ) : (
              <>
                <div className="assistant-chat-messages">
                  {chatLoading ? <LoadingState label="Abriendo conversación..." /> : (
                    allMessages.length ? allMessages.map((item) => (
                      <div
                        key={item.id}
                        className={`message-row ${item.rol === 'usuario' ? 'message-user' : 'message-assistant'}`}
                      >
                        {item.rol === 'asistente' && <div className="message-avatar"><Bot size={16} /></div>}
                        <div className="message-bubble">
                          <p>{item.contenido}</p>
                          {item.fecha_creacion && <small>{dateLabel(item.fecha_creacion)}</small>}
                        </div>
                      </div>
                    )) : (
                      <div className="chat-welcome-message">
                        <div className="chat-bot-large"><Bot size={25} /></div>
                        <strong>¡Hola! Soy tu asistente de RENTIO.</strong>
                        <p>Cuéntame lo que sabes del inmueble; conservaré los datos mientras completamos el registro.</p>
                      </div>
                    )
                  )}
                  {sending && (
                    <div className="message-row message-assistant">
                      <div className="message-avatar"><Bot size={16} /></div>
                      <div className="message-bubble">Estoy procesando tu mensaje…</div>
                    </div>
                  )}
                  <div ref={endRef} />
                </div>

                <div className="assistant-registration-summary">
                  <div className="form-section-title"><Check size={17} /> Resumen de la información</div>
                  <div className="property-detail-meta">
                    {datosKeys.map((key) => {
                      const value = propertyData[key];
                      let labelValue = hasValue(value) ? String(value) : 'Pendiente';
                      if (key === 'precio_mensual' && typeof value === 'number') labelValue = money(value);
                      if (key === 'area_m2' && typeof value === 'number') labelValue = `${value} m²`;
                      if (key === 'parqueadero' && typeof value === 'boolean') labelValue = value ? 'Sí' : 'No';
                      return (
                        <span key={key}>{fieldLabels[key]}: <strong>{labelValue}</strong></span>
                      );
                    })}
                    {Array.isArray(propertyData.caracteristicas) && propertyData.caracteristicas.length > 0 && (
                      <span>Características: <strong>{propertyData.caracteristicas.map(String).join(', ')}</strong></span>
                    )}
                  </div>
                  {!isNeighborhoodValid && hasValue(propertyData.barrio) && (
                    <p className="field-hint">Esta ubicación no aparece en el catálogo oficial. Se guardará con el nombre que indicaste como sector, sin clasificarla como barrio oficial.</p>
                  )}
                  {missingFields.length > 0 && (
                    <p className="field-hint">Falta completar: {missingFields.map((field) => fieldLabels[field] ?? field).join(', ')}. Responde en el chat para continuar.</p>
                  )}
                  {isRegistrationReady && (
                    <>
                      <p className="property-detail-description">
                        Canon indicado por ti: <strong>{money(Number(propertyData.precio_mensual))}</strong>
                        {typeof lastResult?.precio_sugerido === 'number' && (
                          <> · Referencia de mercado: <strong>{money(lastResult.precio_sugerido)}</strong></>
                        )}
                      </p>
                      {lastResult?.descripcion && (
                        <div className="ai-description-preview">
                          <span className="field-label"><Sparkles size={14} /> Descripción llamativa generada por la IA:</span>
                          <p className="generated-description">{lastResult.descripcion}</p>
                        </div>
                      )}
                    </>
                  )}

                  {typeof propertyData.canon_sugerido === 'number' &&
                    propertyData.canon_confirmado !== true &&
                    propertyData.canon_rechazado !== true && (
                      <div className="assistant-canon-choice">
                        <p>
                          Según los datos reales disponibles del mercado, la sugerencia de canon mensual es{' '}
                          <strong>{money(propertyData.canon_sugerido)}</strong>. Tú decides si aceptarla.
                        </p>
                        <div className="modal-actions">
                          <Button
                            type="button"
                            disabled={sending}
                            onClick={() => void sendTurn('Acepto el canon sugerido')}
                          >
                            Aceptar sugerencia
                          </Button>
                          <Button
                            type="button"
                            variant="secondary"
                            disabled={sending}
                            onClick={() => void sendTurn('Rechazo la sugerencia de canon')}
                          >
                            Rechazar e indicar otro canon
                          </Button>
                        </div>
                      </div>
                    )}

                  {propertyData.canon_rechazado === true &&
                    propertyData.canon_confirmado !== true && (
                      <form className="assistant-manual-price" onSubmit={(event) => void submitManualCanon(event)}>
                        <label className="form-field">
                          <span className="field-label">Canon mensual que decides cobrar (COP)</span>
                          <input
                            className="text-input"
                            type="number"
                            min="100000"
                            max="99999999"
                            step="1000"
                            required
                            value={manualCanon}
                            onChange={(event) => setManualCanon(event.target.value)}
                          />
                        </label>
                        <Button type="submit" disabled={sending || !manualCanon}>
                          Confirmar mi canon
                        </Button>
                      </form>
                    )}

                  <div className="assistant-photo-section">
                    <div className="form-section-title"><ImagePlus size={17} /> Fotografías del inmueble</div>
                    <label className="assistant-upload-button">
                      <ImagePlus size={17} /> Adjuntar fotografías (hasta 10)
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        multiple
                        onChange={(event) => {
                          selectImages(event.target.files);
                          event.currentTarget.value = '';
                        }}
                      />
                    </label>
                    <span className="field-hint">JPG, PNG o WEBP; máximo 5 MB por imagen. Se guardarán junto con la propiedad al confirmar.</span>
                    {imagePreviews.length > 0 && (
                      <div className="property-photo-preview-grid">
                        {imagePreviews.map((url, index) => (
                          <div className="property-photo-preview" key={url}>
                            <img src={url} alt={selectedImages[index]?.name || 'Fotografía'} />
                            <button type="button" onClick={() => setSelectedImages((items) => items.filter((_, itemIndex) => itemIndex !== index))}>Quitar</button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <Button
                    type="button"
                    disabled={!isRegistrationReady || saving}
                    onClick={() => void confirmRegistration()}
                  >
                    {saving ? 'Registrando…' : 'Confirmar y registrar propiedad'}
                  </Button>
                </div>

                <form className="chat-composer assistant-composer" onSubmit={sendMessage}>
                  <textarea
                    className="text-input textarea-input"
                    rows={2}
                    value={message}
                    onChange={(event) => setMessage(event.target.value)}
                    maxLength={4000}
                    placeholder="Describe tu inmueble o responde la pregunta del asistente…"
                    disabled={sending || chatLoading}
                  />
                  <button type="submit" disabled={sending || chatLoading || !message.trim()} aria-label="Enviar mensaje">
                    {sending ? <span className="mini-spinner" /> : <Send size={18} />}
                  </button>
                </form>
              </>
            )}
          </Panel>

          <Panel className="assistant-history-panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">HISTORIAL</span>
                <h2>Conversaciones</h2>
                <p>Historial de registros asistidos con IA.</p>
              </div>
              <MessageCircle size={19} />
            </div>

            {conversations.length > 0 ? (
              <div className="chat-conversation-list">
                {conversations.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => void selectConversation(item.id)}
                    className={`conversation-item ${conversation?.id === item.id ? 'conversation-item-active' : ''}`}
                  >
                    <span className="conversation-item-title">{item.propiedad_id ? `Propiedad #${item.propiedad_id}` : `Registro #${item.id}`}</span>
                    <span className="conversation-item-date">{dateLabel(item.fecha_actualizacion)}</span>
                    <StatusBadge value={item.estado} />
                  </button>
                ))}
              </div>
            ) : (
              <div className="assistant-history-empty">
                <Lightbulb size={20} />
                <p>Tus conversaciones de registro aparecerán aquí.</p>
              </div>
            )}
          </Panel>
        </div>
      )}
    </div>
  );
}
