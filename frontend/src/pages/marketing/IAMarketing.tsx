import { useEffect, useRef, useState, type FormEvent } from 'react';
import { ArrowUpRight, Bot, Check, Lightbulb, MessageCircle, Plus, Send, Sparkles, Wand2 } from 'lucide-react';
import { catalogsApi, marketingApi, propertiesApi } from '../../api/services';
import { getApiError } from '../../api/client';
import { dateLabel, money } from '../../lib/format';
import type { ConversacionMarketing, Propiedad } from '../../types';
import { Alert, Button, Field, LoadingState, PageHeader, Panel, StatusBadge } from '../../components/ui';

type ToolKey = 'descripcion' | 'precio' | 'mercado' | 'titulo';
const toolLabels: Record<ToolKey, string> = { descripcion: 'Generar descripción', precio: 'Sugerir canon', mercado: 'Analizar mercado', titulo: 'Mejorar título' };

export default function IAMarketing() {
  const [conversations, setConversations] = useState<ConversacionMarketing[]>([]);
  const [conversation, setConversation] = useState<ConversacionMarketing | null>(null);
  const [properties, setProperties] = useState<Propiedad[]>([]);
  const [selectedProperty, setSelectedProperty] = useState('');
  const [loading, setLoading] = useState(true);
  const [chatLoading, setChatLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [tool, setTool] = useState<ToolKey>('descripcion');
  const [toolLoading, setToolLoading] = useState(false);
  const [toolResult, setToolResult] = useState<Record<string, unknown> | null>(null);
  const [form, setForm] = useState({ barrio: '', tipo: 'apartamento', estrato: '4', habitaciones: '2', banos: '2', area_m2: '', caracteristicas: '', precio_mensual: '', titulo_actual: '' });
  const endRef = useRef<HTMLDivElement>(null);

  async function loadInitial() {
    setLoading(true); setError('');
    try {
      const [chats, props, neighborhoods] = await Promise.all([marketingApi.conversations(), propertiesApi.mine(), catalogsApi.neighborhoods()]);
      setConversations(chats); setProperties(props);
      setForm((current) => ({ ...current, barrio: current.barrio || neighborhoods[0]?.nombre || '' }));
      if (chats.length) {
        const detail = await marketingApi.conversation(chats[0].id);
        setConversation(detail);
      }
    } catch (err) { setError(getApiError(err, 'No fue posible cargar el asistente de marketing.')); }
    finally { setLoading(false); }
  }
  useEffect(() => { loadInitial(); }, []);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }); }, [conversation?.mensajes.length, sending]);

  async function chooseConversation(id: number) {
    setChatLoading(true); setError('');
    try { setConversation(await marketingApi.conversation(id)); }
    catch (err) { setError(getApiError(err, 'No fue posible abrir la conversación.')); }
    finally { setChatLoading(false); }
  }

  async function createConversation() {
    setChatLoading(true); setError(''); setSuccess('');
    try {
      const created = await marketingApi.createConversation(selectedProperty ? Number(selectedProperty) : undefined);
      setConversation(created);
      setConversations((items) => [created, ...items.filter((item) => item.id !== created.id)]);
      setMessage('');
    } catch (err) { setError(getApiError(err, 'No fue posible iniciar una conversación.')); }
    finally { setChatLoading(false); }
  }

  async function sendMessage(event: FormEvent) {
    event.preventDefault(); if (!conversation || !message.trim()) return;
    const content = message.trim(); setSending(true); setMessage(''); setError(''); setSuccess('');
    try {
      await marketingApi.sendMessage(conversation.id, content);
      const [detail, chats] = await Promise.all([marketingApi.conversation(conversation.id), marketingApi.conversations()]);
      setConversation(detail); setConversations(chats);
    } catch (err) { setMessage(content); setError(getApiError(err, 'No fue posible enviar el mensaje al asistente.')); }
    finally { setSending(false); }
  }

  async function applyResult() {
    if (!conversation) return;
    setError(''); setSuccess('');
    try { await marketingApi.apply(conversation.id); setSuccess('La descripción y el canon sugerido se aplicaron a la propiedad asociada.'); const detail = await marketingApi.conversation(conversation.id); setConversation(detail); }
    catch (err) { setError(getApiError(err, 'No fue posible aplicar el resultado. Comprueba que la conversación esté asociada a una propiedad.')); }
  }

  const updateForm = (key: keyof typeof form, value: string) => setForm((current) => ({ ...current, [key]: value }));
  const features = form.caracteristicas.split(',').map((item) => item.trim()).filter(Boolean);

  async function runTool(event: FormEvent) {
    event.preventDefault(); setToolLoading(true); setToolResult(null); setError(''); setSuccess('');
    const common = { barrio: form.barrio.trim(), tipo: form.tipo, estrato: Number(form.estrato), habitaciones: Number(form.habitaciones), banos: Number(form.banos), area_m2: form.area_m2 ? Number(form.area_m2) : undefined, caracteristicas: features };
    try {
      let result: Record<string, unknown>;
      if (tool === 'descripcion') result = await marketingApi.generateDescription({ ...common, precio_mensual: form.precio_mensual ? Number(form.precio_mensual) : undefined, tono: 'atractivo y moderno' });
      else if (tool === 'precio') result = await marketingApi.suggestPrice(common);
      else if (tool === 'mercado') result = await marketingApi.marketAnalysis({ barrio: common.barrio, tipo: common.tipo, estrato: common.estrato });
      else result = await marketingApi.improveTitle({ titulo_actual: form.titulo_actual.trim(), barrio: common.barrio, tipo: common.tipo, caracteristicas_destacadas: features });
      setToolResult(result);
    } catch (err) { setError(getApiError(err, 'No fue posible completar la herramienta de IA.')); }
    finally { setToolLoading(false); }
  }

  const lastResult = conversation?.resultados?.[conversation.resultados.length - 1];

  return <div className="page-stack marketing-page">
    <PageHeader eyebrow="INTELIGENCIA ARTIFICIAL" title="Marketing inmobiliario" description="Prepara publicaciones más atractivas y consulta referencias de canon basadas en los datos de mercado disponibles en RENTIO." />
    {error && <Alert>{error}</Alert>}{success && <Alert variant="success" onClose={() => setSuccess('')}>{success}</Alert>}
    {loading ? <LoadingState label="Preparando herramientas de marketing..." /> : <>
      <div className="marketing-hero"><div className="marketing-hero-icon"><Sparkles size={25} /></div><div><span className="welcome-kicker">RENTIO INTELLIGENCE</span><h2>Publica con más criterio, no a ciegas.</h2><p>Cuéntale al asistente cómo es tu inmueble. Te ayudará a completar la información y, cuando tenga los datos necesarios, generará una descripción y una referencia de canon.</p></div><div className="marketing-hero-tag"><Sparkles size={14} /> Herramientas conectadas a RENTIO</div></div>
      <div className="marketing-tabs"><button className={tool === 'descripcion' ? 'marketing-tab-active' : ''} onClick={() => { setTool('descripcion'); setToolResult(null); }}><Wand2 size={17} /> Herramientas rápidas</button><button className={tool === 'precio' ? 'marketing-tab-active' : ''} onClick={() => { setTool('precio'); setToolResult(null); }}><Lightbulb size={17} /> Estimación de canon</button><button className={tool === 'mercado' ? 'marketing-tab-active' : ''} onClick={() => { setTool('mercado'); setToolResult(null); }}><Sparkles size={17} /> Análisis de mercado</button><button className={tool === 'titulo' ? 'marketing-tab-active' : ''} onClick={() => { setTool('titulo'); setToolResult(null); }}><Wand2 size={17} /> Mejorar título</button><button className="marketing-tab-chat" onClick={() => document.getElementById('marketing-chat')?.scrollIntoView({ behavior: 'smooth' })}><MessageCircle size={17} /> Asistente conversacional</button></div>
      <div className="marketing-tools-layout">
        <Panel className="marketing-tool-form"><div className="panel-heading"><div><span className="eyebrow">HERRAMIENTAS RÁPIDAS</span><h2>{toolLabels[tool]}</h2><p>Usa información real de la propiedad para obtener una respuesta contextual.</p></div></div>
          <form className="modal-form" onSubmit={runTool}>
            <Field label="Barrio de Medellín"><input className="text-input" required minLength={2} value={form.barrio} onChange={(e) => updateForm('barrio', e.target.value)} placeholder="Ej. Belén, Laureles, El Poblado" /></Field>
            <div className="form-grid-two"><Field label="Tipo de inmueble"><select className="text-input" value={form.tipo} onChange={(e) => updateForm('tipo', e.target.value)}><option value="apartamento">Apartamento</option><option value="casa">Casa</option><option value="habitacion">Habitación</option><option value="finca">Finca</option></select></Field><Field label="Estrato"><select className="text-input" value={form.estrato} onChange={(e) => updateForm('estrato', e.target.value)}>{[1,2,3,4,5,6].map((n) => <option key={n}>{n}</option>)}</select></Field></div>
            <div className="form-grid-three"><Field label="Habitaciones"><input className="text-input" type="number" min="1" max="15" value={form.habitaciones} onChange={(e) => updateForm('habitaciones', e.target.value)} /></Field><Field label="Baños"><input className="text-input" type="number" min="0" max="50" value={form.banos} onChange={(e) => updateForm('banos', e.target.value)} /></Field><Field label="Área m²"><input className="text-input" type="number" min="1" step="0.1" value={form.area_m2} onChange={(e) => updateForm('area_m2', e.target.value)} placeholder="Opcional" /></Field></div>
            {tool === 'titulo' && <Field label="Título actual"><input className="text-input" required minLength={3} maxLength={255} value={form.titulo_actual} onChange={(e) => updateForm('titulo_actual', e.target.value)} placeholder="Apartamento en arriendo..." /></Field>}
            {tool === 'descripcion' && <Field label="Canon actual (opcional)"><input className="text-input" type="number" min="0" value={form.precio_mensual} onChange={(e) => updateForm('precio_mensual', e.target.value)} placeholder="2500000" /></Field>}
            <Field label="Características destacadas" hint="Separa cada característica con una coma."><input className="text-input" value={form.caracteristicas} onChange={(e) => updateForm('caracteristicas', e.target.value)} placeholder="Balcón, parqueadero, gimnasio" /></Field>
            <Button type="submit" disabled={toolLoading} className="w-full">{toolLoading ? 'Procesando con IA...' : `Ejecutar: ${toolLabels[tool]}`} <ArrowUpRight size={16} /></Button>
          </form>
          {toolResult && <div className="ai-result-card"><div className="ai-result-heading"><span><Sparkles size={16} /> Resultado generado</span><StatusBadge value="generada" /></div><ResultContent result={toolResult} /></div>}
        </Panel>
        <Panel className="chat-panel" id="marketing-chat"><div className="chat-header"><div className="chat-header-icon"><Bot size={20} /></div><div><h2>Asistente RENTIO</h2><p>Recopilación guiada de datos del inmueble</p></div><span className="chat-secure"><span className="pulse-dot" /> API protegida</span></div>
          <div className="chat-layout">
            <aside className="chat-history"><div className="chat-history-title"><span>CONVERSACIONES</span><button className="icon-button icon-button-accent" onClick={createConversation} title="Nueva conversación"><Plus size={17} /></button></div>
              <label className="field-mini-label">Asociar a una propiedad (opcional)</label><select className="text-input chat-property-select" value={selectedProperty} onChange={(e) => setSelectedProperty(e.target.value)}><option value="">Sin propiedad asociada</option>{properties.map((p) => <option key={p.id} value={p.id}>{p.titulo}</option>)}</select>
              <Button className="w-full chat-new-button" onClick={createConversation}><Plus size={15} /> Nueva conversación</Button>
              <div className="chat-conversation-list">{conversations.map((item) => <button key={item.id} onClick={() => chooseConversation(item.id)} className={`conversation-item ${conversation?.id === item.id ? 'conversation-item-active' : ''}`}><span className="conversation-item-title">{item.propiedad_id ? `Propiedad #${item.propiedad_id}` : `Conversación #${item.id}`}</span><span className="conversation-item-date">{dateLabel(item.fecha_actualizacion)}</span><StatusBadge value={item.estado} /></button>)}</div>
            </aside>
            <div className="chat-main">
              {!conversation ? <div className="chat-empty"><div className="chat-empty-icon"><MessageCircle size={24} /></div><h3>Comienza una conversación</h3><p>Inicia un chat nuevo para que el asistente te ayude a recopilar los datos del inmueble.</p><Button onClick={createConversation}><Plus size={16} /> Iniciar chat</Button></div> : <>
                <div className="chat-messages">{chatLoading ? <LoadingState label="Abriendo conversación..." /> : conversation.mensajes.length ? conversation.mensajes.map((item) => <div key={item.id} className={`message-row ${item.rol === 'usuario' ? 'message-user' : 'message-assistant'}`}><div className="message-avatar">{item.rol === 'usuario' ? 'TÚ' : <Bot size={16} />}</div><div className="message-bubble"><p>{item.contenido}</p><small>{dateLabel(item.fecha_creacion)}</small></div></div>) : <div className="chat-welcome-message"><div className="chat-bot-large"><Bot size={25} /></div><strong>¡Hola! Soy tu asistente de marketing inmobiliario.</strong><p>Cuéntame sobre tu propiedad. Podemos comenzar con el barrio, el tipo de inmueble, las habitaciones y los detalles que la hacen especial.</p><div className="suggestion-prompts"><button onClick={() => setMessage('Tengo un apartamento en Laureles con dos habitaciones y dos baños.')}>Tengo un apartamento en Laureles...</button><button onClick={() => setMessage('Quiero conocer el canon recomendado para una casa en Belén.')}>Quiero estimar un canon...</button></div></div>}
                  <div ref={endRef} />
                </div>
                {lastResult && <div className="chat-generated-result"><div className="ai-result-heading"><span><Check size={16} /> Resultado listo</span><StatusBadge value={conversation.estado} /></div><p className="generated-description">{lastResult.descripcion}</p><div className="generated-price-row"><div><small>CANON SUGERIDO</small><strong>{money(lastResult.precio_sugerido)}</strong></div><div><small>RANGO DE REFERENCIA</small><strong>{money(lastResult.precio_minimo)} – {money(lastResult.precio_maximo)}</strong></div></div>{conversation.propiedad_id && <Button size="sm" onClick={applyResult}><Check size={15} /> Aplicar a mi propiedad</Button>}</div>}
                <form className="chat-composer" onSubmit={sendMessage}><input value={message} onChange={(e) => setMessage(e.target.value)} maxLength={4000} placeholder="Escribe los detalles de tu inmueble..." disabled={sending || chatLoading} /><button type="submit" disabled={sending || !message.trim()} aria-label="Enviar mensaje">{sending ? <span className="mini-spinner" /> : <Send size={18} />}</button></form>
              </>}
            </div>
          </div>
        </Panel>
      </div>
      <div className="market-disclaimer"><Lightbulb size={17} /><span>Las referencias de canon se calculan con datos de avisos de arriendo de Medellín. Representan precios solicitados, no valores de contratos cerrados; consulta los metadatos y limitaciones del resultado antes de tomar decisiones.</span></div>
    </>}
  </div>;
}

function ResultContent({ result }: { result: Record<string, unknown> }) {
  const description = result.descripcion ?? result.descripcion_sugerida;
  const price = result.precio_sugerido ?? result.precio_estimado;
  const min = result.precio_minimo;
  const max = result.precio_maximo;
  const hasRange = (typeof min === 'number' && Number.isFinite(min)) || (typeof max === 'number' && Number.isFinite(max));
  const points = Array.isArray(result.puntos_destacados) ? result.puntos_destacados : Array.isArray(result.titulos_sugeridos) ? result.titulos_sugeridos : [];
  const analysis = result.analisis ?? result.analisis_resumido ?? result.recomendacion;
  const market = result.nivel_demanda;
  const trend = result.tendencia_mercado;
  const propertyType = result.tipo_inmueble;
  const predominantStratum = result.estrato_predominante;
  return <div className="ai-result-content">
    {typeof description === 'string' && <p>{description}</p>}
    {typeof price === 'number' && <div className="ai-price-block"><small>PRECIO SUGERIDO</small><strong>{money(Number(price))}</strong>{hasRange && <span>{typeof min === 'number' ? money(min) : 'Sin mínimo'} – {typeof max === 'number' ? money(max) : 'Sin máximo'}</span>}</div>}
    {typeof market === 'string' && <p><strong>Nivel de demanda:</strong> {market}</p>}
    {typeof analysis === 'string' && <p>{analysis}</p>}
    {typeof trend === 'string' && <p><strong>Tendencia:</strong> {trend}</p>}
    {typeof propertyType === 'string' && <p><strong>Tipo de inmueble:</strong> {propertyType}</p>}
    {typeof predominantStratum === 'number' && <p><strong>Estrato predominante:</strong> {predominantStratum}</p>}
    {points.length > 0 && <ul>{points.map((point, index) => <li key={index}>{String(point)}</li>)}</ul>}
    {result.metadatos_calculo && typeof result.metadatos_calculo === 'object' && <details className="metadata-details"><summary>Ver metodología y datos utilizados</summary><pre>{JSON.stringify(result.metadatos_calculo, null, 2)}</pre></details>}
    {result.zona && <p><strong>Zona analizada:</strong> {String(result.zona)}</p>}
    {result.tiempo_promedio_vacancia_dias !== undefined && <p><strong>Vacancia promedio:</strong> {String(result.tiempo_promedio_vacancia_dias)} días</p>}
  </div>;
}
