import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Bot,
  Check,
  ImagePlus,
  Lightbulb,
  MessageCircle,
  Plus,
  Send,
  Sparkles,
  Wand2,
} from 'lucide-react';

import './AsistenteIA.css';
import { getApiError } from '../../api/client';
import { catalogsApi, marketingApi, propertiesApi } from '../../api/services';
import { dateLabel, money } from '../../lib/format';
import type {
  Barrio,
  ConversacionMarketing,
  MensajeMarketing,
  Propiedad,
} from '../../types';
import {
  Alert,
  Button,
  LoadingState,
  PageHeader,
  Panel,
  StatusBadge,
} from '../../components/ui';

type Mode = 'registro' | 'marketing';
type MarketingTool = 'descripcion' | 'precio' | 'mercado' | 'titulo';

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

const toolLabels: Record<MarketingTool, string> = {
  descripcion: 'Generar descripción',
  precio: 'Sugerir canon',
  mercado: 'Analizar mercado',
  titulo: 'Mejorar título',
};

const normalize = (value: string) =>
  value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').trim().toLowerCase();

function hasValue(value: unknown) {
  return value !== undefined && value !== null && value !== '';
}

function getToolReply(tool: MarketingTool, result: Record<string, unknown>) {
  if (tool === 'descripcion' && typeof result.descripcion === 'string') {
    return result.descripcion;
  }
  if (tool === 'titulo' && Array.isArray(result.titulos_sugeridos)) {
    return result.titulos_sugeridos.map(String).join('\n');
  }
  if (tool === 'precio' && typeof result.precio_sugerido === 'number') {
    return `El canon de referencia es ${money(result.precio_sugerido)}.`;
  }
  if (tool === 'mercado' && typeof result.recomendacion === 'string') {
    return `${result.nivel_demanda ? `Demanda: ${result.nivel_demanda}. ` : ''}${result.recomendacion}`;
  }
  return 'La herramienta respondió, pero no devolvió contenido para mostrar.';
}

export default function AsistenteIA() {
  const [searchParams, setSearchParams] = useSearchParams();
  const mode: Mode = searchParams.get('modo') === 'registro' ? 'registro' : 'marketing';
  const [properties, setProperties] = useState<Propiedad[]>([]);
  const [neighborhoods, setNeighborhoods] = useState<Barrio[]>([]);
  const [conversations, setConversations] = useState<ConversacionMarketing[]>([]);
  const [conversation, setConversation] = useState<ConversacionMarketing | null>(null);
  const [selectedProperty, setSelectedProperty] = useState('');
  const [missingFields, setMissingFields] = useState<string[]>([...REQUIRED_FIELDS]);
  const [message, setMessage] = useState('');
  const [localMessages, setLocalMessages] = useState<MensajeMarketing[]>([]);
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const [toolResult, setToolResult] = useState<Record<string, unknown> | null>(null);
  const [activeTool, setActiveTool] = useState<MarketingTool | null>(null);
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
        const [props, chats, barrios] = await Promise.all([
          propertiesApi.mine(),
          marketingApi.conversations(),
          catalogsApi.neighborhoods(),
        ]);
        if (!active) return;
        setProperties(props);
        setConversations(chats);
        setNeighborhoods(barrios);
        setSelectedProperty(props[0] ? String(props[0].id) : '');
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
  }, [conversation?.mensajes.length, localMessages.length, sending]);

  const property = properties.find((item) => String(item.id) === selectedProperty) ?? null;
  const propertyData = conversation?.datos_recopilados ?? {};
  const lastResult = conversation?.resultados?.[conversation.resultados.length - 1] ?? null;
  const allMessages = useMemo(
    () => [...(conversation?.mensajes ?? []), ...localMessages],
    [conversation?.mensajes, localMessages],
  );
  const isNeighborhoodValid = neighborhoods.some(
    (item) => normalize(item.nombre) === normalize(String(propertyData.barrio ?? '')),
  );
  const isRegistrationReady =
    Boolean(conversation) &&
    conversation?.estado === 'lista' &&
    missingFields.length === 0 &&
    REQUIRED_FIELDS.every((field) => hasValue(propertyData[field])) &&
    isNeighborhoodValid &&
    Number(propertyData.precio_mensual) > 0;

  function changeMode(nextMode: Mode) {
    setSearchParams(nextMode === 'registro' ? { modo: 'registro' } : {});
    setConversation(null);
    setLocalMessages([]);
    setToolResult(null);
    setError('');
    setSuccess('');
  }

  async function startConversation() {
    if (mode === 'marketing' && !selectedProperty) {
      setError('Selecciona una de tus propiedades para iniciar el marketing.');
      return;
    }
    setChatLoading(true);
    setError('');
    setSuccess('');
    setLocalMessages([]);
    setMessage('');
    try {
      const created = await marketingApi.createConversation(
        mode === 'marketing' ? Number(selectedProperty) : undefined,
      );
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
    setLocalMessages([]);
    try {
      const detail = await marketingApi.conversation(id);
      setConversation(detail);
      setSelectedProperty(detail.propiedad_id ? String(detail.propiedad_id) : '');
      setMissingFields(
        REQUIRED_FIELDS.filter((field) => !hasValue(detail.datos_recopilados?.[field])),
      );
    } catch (err) {
      setError(getApiError(err, 'No fue posible abrir la conversación.'));
    } finally {
      setChatLoading(false);
    }
  }

  function addLocalExchange(prompt: string, reply: string) {
    const now = new Date().toISOString();
    setLocalMessages((items) => [
      ...items,
      { id: -Date.now(), rol: 'usuario', contenido: prompt, fecha_creacion: now },
      { id: -(Date.now() + 1), rol: 'asistente', contenido: reply, fecha_creacion: now },
    ]);
  }

  async function runMarketingTool(tool: MarketingTool, prompt = toolLabels[tool]) {
    if (!property) {
      setError('Selecciona una propiedad de tu inventario antes de generar contenido.');
      return false;
    }
    if (!property.barrio?.nombre) {
      setError('Esta propiedad no tiene un barrio validado. Actualízala antes de usar las herramientas de IA.');
      return false;
    }

    setActiveTool(tool);
    setError('');
    setSuccess('');
    setToolResult(null);
    if (!conversation) {
      try {
        const created = await marketingApi.createConversation(Number(selectedProperty));
        setConversation(created);
        setConversations((items) => [created, ...items.filter((item) => item.id !== created.id)]);
      } catch (err) {
        setError(getApiError(err, 'No fue posible iniciar la conversación de marketing.'));
        return false;
      }
    }
    const common = {
      barrio: property.barrio.nombre,
      tipo: property.tipo,
      estrato: property.estrato,
      habitaciones: property.habitaciones,
      banos: property.banos,
      area_m2: property.area_m2 ?? undefined,
      caracteristicas: property.caracteristicas.map((item) => item.nombre),
    };
    try {
      let result: Record<string, unknown>;
      if (tool === 'descripcion') {
        result = await marketingApi.generateDescription({
          ...common,
          precio_mensual: property.precio_mensual,
          tono: 'atractivo y moderno',
        });
      } else if (tool === 'precio') {
        result = await marketingApi.suggestPrice({
          ...common,
          parqueadero: property.caracteristicas.some((item) =>
            normalize(item.nombre).includes('parqueadero'),
          ),
        });
      } else if (tool === 'mercado') {
        result = await marketingApi.marketAnalysis({
          barrio: common.barrio,
          tipo: common.tipo,
          estrato: common.estrato,
        });
      } else {
        result = await marketingApi.improveTitle({
          titulo_actual: property.titulo,
          barrio: common.barrio,
          tipo: common.tipo,
          caracteristicas_destacadas: common.caracteristicas,
        });
      }
      setToolResult(result);
      addLocalExchange(prompt, getToolReply(tool, result));
      return true;
    } catch (err) {
      setError(getApiError(err, 'No fue posible completar la herramienta de marketing.'));
      return false;
    } finally {
      setActiveTool(null);
    }
  }

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    if (!conversation || !message.trim() || sending || chatLoading) return;
    const content = message.trim();
    setSending(true);
    setMessage('');
    setError('');
    try {
      if (mode === 'marketing') {
        const normalized = normalize(content);
        const requestedTool: MarketingTool | null =
          /descripcion|anuncio|publicidad|publicacion|copy|texto comercial/.test(normalized)
            ? 'descripcion'
            : /titulo|titular/.test(normalized)
              ? 'titulo'
              : /canon|precio|estimar|estimacion/.test(normalized)
                ? 'precio'
                : /mercado|demanda|vacancia/.test(normalized)
                  ? 'mercado'
                  : null;
        if (requestedTool) {
          await runMarketingTool(requestedTool, content);
          return;
        }
      }

      const response = await marketingApi.sendMessage(conversation.id, content);
      const [detail, chats] = await Promise.all([
        marketingApi.conversation(conversation.id),
        marketingApi.conversations(),
      ]);
      setConversation(detail);
      setConversations(chats);
      setMissingFields(response.datos_faltantes);
    } catch (err) {
      setMessage(content);
      setError(getApiError(err, 'No fue posible enviar el mensaje. Revisa la conexión con el servicio de IA.'));
    } finally {
      setSending(false);
    }
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
      setSuccess(`“${created.titulo}” quedó registrada con ${created.imagenes.length} fotografía(s).`);
      setSelectedImages([]);
      setConversation(await marketingApi.conversation(conversation.id));
      const [props, chats] = await Promise.all([
        propertiesApi.mine(),
        marketingApi.conversations(),
      ]);
      setProperties(props);
      setConversations(chats);
    } catch (err) {
      setError(getApiError(err, 'No fue posible confirmar el registro. No se guardó la propiedad.'));
    } finally {
      setSaving(false);
    }
  }

  async function applyResult() {
    if (!conversation?.propiedad_id) return;
    setError('');
    setSuccess('');
    try {
      await marketingApi.apply(conversation.id);
      setSuccess('La descripción y el canon sugerido se aplicaron a la propiedad asociada.');
      setConversation(await marketingApi.conversation(conversation.id));
      setProperties(await propertiesApi.mine());
    } catch (err) {
      setError(getApiError(err, 'No fue posible aplicar el resultado a la propiedad.'));
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
  const visibleConversations = conversations;

  return (
    <div className="page-stack assistant-page">
      <PageHeader
        eyebrow="RENTIO INTELLIGENCE"
        title="Asistente IA"
        description="Registra un inmueble conversando o prepara contenido de marketing para una propiedad de tu inventario."
      />

      <div className="assistant-mode-switch" role="tablist" aria-label="Modo del asistente">
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'registro'}
          className={mode === 'registro' ? 'assistant-mode-active' : ''}
          onClick={() => changeMode('registro')}
        >
          <MessageCircle size={17} /> Registrar propiedad
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'marketing'}
          className={mode === 'marketing' ? 'assistant-mode-active' : ''}
          onClick={() => changeMode('marketing')}
        >
          <Sparkles size={17} /> Marketing de propiedades
        </button>
      </div>

      {error && <Alert>{error}</Alert>}
      {success && <Alert variant="success" onClose={() => setSuccess('')}>{success}</Alert>}

      {loading ? <LoadingState label="Preparando el asistente..." /> : (
        <div className="assistant-layout">
          <Panel className="assistant-chat-panel">
            <div className="chat-header">
              <div className="chat-header-icon"><Bot size={20} /></div>
              <div>
                <h2>{mode === 'registro' ? 'Registro conversacional' : 'Asistente de marketing'}</h2>
                <p>{mode === 'registro'
                  ? 'Describe el inmueble con tus palabras; no necesitas completar formularios.'
                  : 'Pide contenido para tu propiedad o elige una herramienta de marketing.'}</p>
              </div>
              <span className="chat-secure"><span className="pulse-dot" /> RENTIO AI</span>
            </div>

            <div className="assistant-toolbar">
              {mode === 'marketing' && (
                <label className="assistant-property-picker">
                  <span>Propiedad</span>
                  <select
                    className="text-input"
                    value={selectedProperty}
                    onChange={(event) => {
                      setSelectedProperty(event.target.value);
                      setConversation(null);
                      setLocalMessages([]);
                      setToolResult(null);
                    }}
                  >
                    <option value="">Selecciona un inmueble</option>
                    {properties.map((item) => (
                      <option key={item.id} value={item.id}>{item.titulo}</option>
                    ))}
                  </select>
                </label>
              )}
              <Button
                type="button"
                variant="secondary"
                disabled={chatLoading || (mode === 'marketing' && !selectedProperty)}
                onClick={() => void startConversation()}
              >
                <Plus size={16} /> Nueva conversación
              </Button>
            </div>

            {mode === 'marketing' && (
              <div className="assistant-tool-actions">
                {(Object.keys(toolLabels) as MarketingTool[]).map((tool) => (
                  <button
                    key={tool}
                    type="button"
                    className="assistant-tool-chip"
                    disabled={Boolean(activeTool) || !property}
                    onClick={() => void runMarketingTool(tool)}
                  >
                    {activeTool === tool ? <span className="mini-spinner" /> : <Wand2 size={15} />}
                    {toolLabels[tool]}
                  </button>
                ))}
              </div>
            )}

            {!conversation ? (
              <div className="assistant-empty">
                <div className="chat-bot-large"><Bot size={25} /></div>
                <strong>
                  {mode === 'registro'
                    ? '¡Hola! Cuéntame cómo es tu inmueble.'
                    : property
                      ? `¿Qué contenido necesitas para “${property.titulo}”?`
                      : 'Selecciona una propiedad para comenzar.'}
                </strong>
                <p>
                  {mode === 'registro'
                    ? 'Puedes compartir todos los datos en un solo mensaje. Te preguntaré únicamente lo que haga falta y podrás corregir cualquier dato conversando.'
                    : 'Puedes solicitar una descripción, mejorar el título, estimar el canon o revisar el mercado.'}
                </p>
                {mode === 'registro' ? (
                  <Button onClick={() => void startConversation()} disabled={chatLoading}>
                    <MessageCircle size={16} /> Comenzar registro
                  </Button>
                ) : (
                  <Button onClick={() => void startConversation()} disabled={chatLoading || !property}>
                    <MessageCircle size={16} /> Iniciar chat de marketing
                  </Button>
                )}
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
                        <strong>{mode === 'registro' ? '¡Hola! Soy tu asistente de RENTIO.' : 'Conversemos sobre tu publicación.'}</strong>
                        <p>{mode === 'registro'
                          ? 'Cuéntame lo que sabes del inmueble; conservaré los datos mientras completamos el registro.'
                          : 'Escribe qué contenido necesitas. También puedes usar los accesos rápidos de marketing.'}</p>
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

                {mode === 'marketing' && lastResult && (
                  <div className="assistant-result-card">
                    <div className="ai-result-heading"><span><Check size={16} /> Resultado de la conversación</span><StatusBadge value={conversation.estado} /></div>
                    <p className="generated-description">{lastResult.descripcion}</p>
                    {typeof lastResult.precio_sugerido === 'number' && (
                      <div className="generated-price-row">
                        <div><small>CANON SUGERIDO</small><strong>{money(lastResult.precio_sugerido)}</strong></div>
                        <div><small>RANGO DE REFERENCIA</small><strong>{money(lastResult.precio_minimo ?? 0)} – {money(lastResult.precio_maximo ?? 0)}</strong></div>
                      </div>
                    )}
                    {conversation.propiedad_id && (
                      <Button size="sm" onClick={() => void applyResult()}><Check size={15} /> Aplicar a mi propiedad</Button>
                    )}
                  </div>
                )}

                {mode === 'registro' && (
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
                      <p className="field-hint">El barrio extraído debe coincidir con uno del catálogo de RENTIO. Corrígelo escribiendo su nombre en el chat.</p>
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
                        {lastResult?.descripcion && <p className="generated-description">{lastResult.descripcion}</p>}
                      </>
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
                )}

                <form className="chat-composer assistant-composer" onSubmit={sendMessage}>
                  <textarea
                    className="text-input textarea-input"
                    rows={2}
                    value={message}
                    onChange={(event) => setMessage(event.target.value)}
                    maxLength={4000}
                    placeholder={mode === 'registro'
                      ? 'Describe tu inmueble o responde la pregunta…'
                      : 'Ej. Genera una descripción atractiva para mi propiedad…'}
                    disabled={sending || chatLoading || Boolean(activeTool)}
                  />
                  <button type="submit" disabled={sending || chatLoading || !message.trim() || Boolean(activeTool)} aria-label="Enviar mensaje">
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
                <p>Registro y marketing comparten este mismo asistente.</p>
              </div>
              <MessageCircle size={19} />
            </div>
            {mode === 'marketing' && toolResult && (
              <div className="ai-result-card">
                <div className="ai-result-heading"><span><Sparkles size={16} /> {activeTool ? 'Procesando' : 'Contenido generado'}</span></div>
                <ResultContent result={toolResult} />
              </div>
            )}
            {visibleConversations.length > 0 ? (
              <div className="chat-conversation-list">
                {visibleConversations.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => void selectConversation(item.id)}
                    className={`conversation-item ${conversation?.id === item.id ? 'conversation-item-active' : ''}`}
                  >
                    <span className="conversation-item-title">{item.propiedad_id ? `Propiedad #${item.propiedad_id}` : `Conversación #${item.id}`}</span>
                    <span className="conversation-item-date">{dateLabel(item.fecha_actualizacion)}</span>
                    <StatusBadge value={item.estado} />
                  </button>
                ))}
              </div>
            ) : (
              <div className="assistant-history-empty">
                <Lightbulb size={20} />
                <p>Tus conversaciones aparecerán aquí.</p>
              </div>
            )}
            {mode === 'marketing' && (
              <p className="market-disclaimer">Las referencias de canon usan avisos de arriendo disponibles en RENTIO; no representan precios de contratos cerrados.</p>
            )}
          </Panel>
        </div>
      )}
    </div>
  );
}

function ResultContent({ result }: { result: Record<string, unknown> }) {
  const description = result.descripcion ?? result.descripcion_sugerida;
  const price = result.precio_sugerido ?? result.precio_estimado;
  const minimum = result.precio_minimo;
  const maximum = result.precio_maximo;
  const points = Array.isArray(result.puntos_destacados)
    ? result.puntos_destacados
    : Array.isArray(result.titulos_sugeridos)
      ? result.titulos_sugeridos
      : [];
  const metadata = result.metadatos_calculo;
  return (
    <div className="ai-result-content">
      {typeof description === 'string' && <p>{description}</p>}
      {typeof price === 'number' && <div className="ai-price-block"><small>PRECIO SUGERIDO</small><strong>{money(price)}</strong></div>}
      {typeof minimum === 'number' && typeof maximum === 'number' && (
        <p>Rango de referencia: {money(minimum)} – {money(maximum)}</p>
      )}
      {typeof result.nivel_demanda === 'string' && <p><strong>Nivel de demanda:</strong> {result.nivel_demanda}</p>}
      {typeof result.tendencia_mercado === 'string' && <p><strong>Tendencia:</strong> {result.tendencia_mercado}</p>}
      {typeof result.recomendacion === 'string' && <p>{result.recomendacion}</p>}
      {points.length > 0 && <ul>{points.map((point, index) => <li key={index}>{String(point)}</li>)}</ul>}
      {metadata !== null && typeof metadata === 'object' ? (
        <details className="metadata-details"><summary>Ver metodología y datos</summary><pre>{JSON.stringify(metadata, null, 2)}</pre></details>
      ) : null}
    </div>
  );
}
