# Kafka Video Processing Service

## 📋 Descripción General

Este proyecto implementa un servicio de procesamiento de videos basado en Apache Kafka que permite recibir URLs de videos a través de una API REST, procesarlos de manera asíncrona y distribuida, y enviar los resultados a un backend configurado.

### Componentes Principales

- **Kafka Cluster**: 3 brokers con KRaft (sin Zookeeper) para alta disponibilidad
- **Producer API**: API REST en FastAPI que recibe solicitudes de procesamiento
- **Consumer**: Servicio que procesa los videos de manera asíncrona
- **Kafka UI**: Interfaz web para monitorear el cluster de Kafka

## 🏗️ Arquitectura del Sistema

```mermaid
graph TB
    Client[Cliente HTTP] --> API[Producer API :8080]
    API --> Kafka[Kafka Cluster<br/>3 Brokers]
    Kafka --> Consumer[Video Consumer]
    Consumer --> Backend[Backend Service<br/>:8040]
    
    subgraph "Kafka Cluster"
        B1[Broker 1 :9092]
        B2[Broker 2 :9093] 
        B3[Broker 3 :9094]
    end
    
    Kafka --> UI[Kafka UI :8081]
```

### Flujo de Procesamiento

1. **Cliente** envía POST con URL del video a la API Producer
2. **Producer** valida el payload y publica mensaje en Kafka topic
3. **Consumer** consume mensaje del topic y descarga/procesa el video
4. **Consumer** envía resultado al Backend configurado
5. **Backend** recibe los datos procesados para su posterior uso

## 📋 Prerrequisitos

- **Windows 10/11** con PowerShell 7.x
- **Docker Desktop** con Docker Compose v2
- **WSL 2** (recomendado para mejor rendimiento)
- **Recursos mínimos**: 4GB RAM, 2 CPUs, 10GB espacio libre
- **Puertos libres**: 8080, 8081, 9092, 9093, 9094

### Verificar Instalación

```powershell
# Verificar Docker
docker --version
docker compose version

# Verificar PowerShell
$PSVersionTable.PSVersion
```

## 🚀 Instalación y Despliegue

### 1. Clonar y Navegar al Proyecto

```powershell
Set-Location C:\Users\Usuario\Desktop\projects\kafkaservice
```

### 2. Configurar Variables de Entorno

El proyecto incluye un archivo `.env` preconfigurado. Revisa y ajusta si es necesario:

```powershell
# Ver configuración actual
Get-Content .env
```

### 3. Levantar el Stack Completo

```powershell
# Construir imágenes locales
docker compose build

# Levantar todos los servicios
docker compose up -d

# Verificar estado de los servicios
docker compose ps
```

### 4. Verificar que Todo Funciona

```powershell
# Verificar logs de inicialización
docker compose logs init-topics

# Verificar APIs disponibles
curl http://localhost:8080/health
curl http://localhost:8081  # Kafka UI

# Ver topics creados
docker compose exec broker1 kafka-topics --list --bootstrap-server broker1:9092
```

## 🛠️ Servicios del Docker Compose

### Kafka Cluster (3 Brokers)

- **Broker 1**: Puerto 9092, nodo líder del cluster
- **Broker 2**: Puerto 9093, réplica
- **Broker 3**: Puerto 9094, réplica
- **Configuración**: KRaft mode, replicación factor 3, particiones 3
- **Volúmenes**: Datos persistentes para cada broker

### Init Topics

- **Propósito**: Crear automáticamente el topic `video-topic`
- **Configuración**: 3 particiones, factor de replicación 3
- **Ejecución**: Una sola vez al inicio del stack

### Producer API (FastAPI)

- **Puerto**: 8080
- **Endpoints**: `/health`, `/publish`
- **Función**: Recibir URLs de videos y publicarlas en Kafka
- **Volúmenes**: Código fuente mapeado para desarrollo

### Consumer

- **Función**: Procesar mensajes de video de manera asíncrona
- **Configuración**: Group ID `video-group`, procesamiento en orden
- **Backend**: Configurable vía `BACKEND_ENDPOINT`

### Kafka UI

- **Puerto**: 8081
- **Función**: Interfaz web para monitoreo del cluster
- **Acceso**: http://localhost:8081

## 📡 API del Producer

### Base URL
```
http://localhost:8080
```

### Endpoints

#### Health Check
```http
GET /health
```

**Respuesta:**
```json
{
  "status": "ok"
}
```

#### Publicar Video para Procesamiento
```http
POST /publish
Content-Type: application/json
```

**Cuerpo de la Petición:**
```json
{
  "video_url": "https://firebasestorage.googleapis.com/v0/b/mybucket/o/videos%2Fgame1.mp4?alt=media&token=abc123",
  "metadata": {
    "source": "uploader-web",
    "priority": "high",
    "callback_url": "https://myapi.com/webhooks/video-processed"
  }
}
```

**Respuesta Exitosa (200):**
```json
{
  "status": "ok",
  "topic": "video-topic",
  "partition": 1,
  "offset": 42
}
```

**Respuesta de Error (500):**
```json
{
  "detail": "Invalid video URL format"
}
```

### Ejemplos de Uso

#### PowerShell
```powershell
$body = @{
    video_url = "https://firebasestorage.googleapis.com/v0/b/mybucket/o/videos%2Ftest.mp4?alt=media&token=xyz"
    metadata = @{
        source = "api-test"
        priority = "normal"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8080/publish" -Method Post -Body $body -ContentType "application/json"
```

#### cURL
```bash
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "metadata": {"source": "curl-test"}
  }'
```

## 📝 Formato de Mensajes Kafka

### Topic: `video-topic`

#### Mensaje de Entrada (Producer → Kafka)

```json
{
  "video_url": "https://firebasestorage.googleapis.com/v0/b/mybucket/o/videos%2Fgame1.mp4?alt=media&token=abc",
  "metadata": {
    "source": "uploader-web",
    "priority": "normal",
    "callback_url": "https://api.example.com/webhook"
  },
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "produced_at": 1699123456.789
}
```

#### Key del Mensaje
La clave se genera a partir de la URL del video para garantizar que videos del mismo origen se procesen en orden en la misma partición.

### Payload al Backend

El consumer envía al backend configurado:

```json
{
  "video_url": "https://firebasestorage.googleapis.com/v0/b/mybucket/o/videos%2Fgame1.mp4?alt=media&token=abc",
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "produced_at": 1699123456.789,
  "metadata": {
    "source": "uploader-web",
    "priority": "normal"
  },
  "kafka_partition": 1,
  "kafka_offset": 42
}
```

## 🔄 Flujo de Procesamiento Detallado

### 1. Recepción de Petición
- Cliente HTTP POST → Producer API `:8080/publish`
- Validación del payload usando Pydantic
- Generación de `message_id` único y timestamp

### 2. Publicación en Kafka
- Envío al topic `video-topic`
- Key basada en URL para ordenamiento
- Configuración de retry y idempotencia
- Confirmación de escritura (acks=all)

### 3. Consumo y Procesamiento
- Consumer lee mensaje con group ID `video-group`
- Validación del esquema del mensaje
- Retry automático en fallos transitorios
- Circuit breaker para fallos consecutivos

### 4. Envío al Backend
- HTTP POST al `BACKEND_ENDPOINT` configurado
- Retry con backoff exponencial
- Commit del offset solo tras éxito del backend
- Manejo de errores 4xx vs 5xx

### 5. Finalización
- Offset committeado en Kafka
- Mensaje marcado como procesado
- Log de métricas y trazabilidad

## ⚙️ Variables de Entorno

### Kafka Configuration
| Variable | Descripción | Valor por Defecto |
|----------|-------------|------------------|
| `KAFKA_BOOTSTRAP` | Brokers de Kafka | `broker1:9092,broker2:9092,broker3:9092` |
| `KAFKA_TOPIC` | Topic principal | `video-topic` |
| `KAFKA_GROUP_ID` | Group ID del consumer | `video-group` |

### Producer Configuration
| Variable | Descripción | Valor por Defecto |
|----------|-------------|------------------|
| `PRODUCER_CLIENT_ID` | ID del cliente productor | `video-producer-1` |
| `PRODUCER_PORT` | Puerto del API | `8080` |
| `USE_VIDEO_AS_KEY` | Usar URL como key | `true` |

### Consumer Configuration  
| Variable | Descripción | Valor por Defecto |
|----------|-------------|------------------|
| `CONSUMER_CLIENT_ID` | ID del cliente consumer | `video-consumer-1` |
| `BACKEND_ENDPOINT` | URL del backend destino | `http://backend:8040/process_video` |

### Personalización

```powershell
# Cambiar el endpoint del backend
$env:BACKEND_ENDPOINT = "http://mi-backend:8080/procesar"

# Cambiar el nombre del topic
$env:KAFKA_TOPIC = "mi-topic-videos"

# Reiniciar servicios con nueva configuración
docker compose restart producer consumer
```

## 📊 Monitoreo y Observabilidad

### Verificar Estado de Servicios

```powershell
# Estado general
docker compose ps

# Logs en tiempo real
docker compose logs -f producer
docker compose logs -f consumer
docker compose logs -f broker1

# Healthchecks
curl http://localhost:8080/health
```

### Kafka UI - Monitoring Dashboard

Accede a http://localhost:8081 para:
- Ver topics, particiones y mensajes
- Monitorear consumer groups y lag
- Inspeccionar mensajes individuales
- Ver métricas del cluster

### Comandos Útiles de Kafka

```powershell
# Listar topics
docker compose exec broker1 kafka-topics --list --bootstrap-server broker1:9092

# Describir topic
docker compose exec broker1 kafka-topics --describe --topic video-topic --bootstrap-server broker1:9092

# Ver mensajes en tiempo real
docker compose exec broker1 kafka-console-consumer --topic video-topic --from-beginning --bootstrap-server broker1:9092

# Ver consumer groups
docker compose exec broker1 kafka-consumer-groups --list --bootstrap-server broker1:9092

# Ver lag del consumer group
docker compose exec broker1 kafka-consumer-groups --describe --group video-group --bootstrap-server broker1:9092
```

## 🛠️ Troubleshooting

### Problemas Comunes

#### Servicios no inician
```powershell
# Verificar puertos ocupados
netstat -an | findstr ":8080"
netstat -an | findstr ":9092"

# Ver logs detallados
docker compose logs broker1
docker compose logs producer
```

#### Consumer no procesa mensajes
```powershell
# Verificar conexión al backend
curl -X POST http://backend:8040/process_video -H "Content-Type: application/json" -d "{}"

# Reset consumer offset (CUIDADO: solo desarrollo)
docker compose exec broker1 kafka-consumer-groups --reset-offsets --to-earliest --group video-group --topic video-topic --bootstrap-server broker1:9092
```

#### Errores de conexión Kafka
```powershell
# Verificar DNS interno
docker compose exec producer nslookup broker1
docker compose exec consumer nslookup broker1

# Reiniciar cluster Kafka
docker compose restart broker1 broker2 broker3
```

### Logs de Error Típicos

- **"Connection timeout"**: Verificar red Docker y DNS
- **"Topic does not exist"**: Ejecutar init-topics manualmente
- **"No route to host"**: Verificar firewall y puertos
- **"Serialization error"**: Verificar formato JSON del payload

## 🏃‍♂️ Ejemplos de Uso Completos

### Ejemplo 1: Procesamiento Básico

```powershell
# 1. Enviar video para procesamiento
$response = Invoke-RestMethod -Uri "http://localhost:8080/publish" -Method Post -Body '{
  "video_url": "https://sample-videos.com/zip/10/mp4/mp4/SampleVideo_1280x720_1mb.mp4",
  "metadata": {"test": true}
}' -ContentType "application/json"

Write-Host "Video enviado: Partition $($response.partition), Offset $($response.offset)"

# 2. Ver el mensaje en Kafka
docker compose exec broker1 kafka-console-consumer --topic video-topic --from-beginning --bootstrap-server broker1:9092 --max-messages 1

# 3. Ver logs del consumer procesando
docker compose logs -f consumer
```

### Ejemplo 2: Monitoreo en Kafka UI

1. Abrir http://localhost:8081
2. Navegar a Topics → video-topic
3. Ver mensajes en "Messages" tab
4. Revisar Consumer Groups para ver el progreso

### Ejemplo 3: Simulación de Carga

```powershell
# Script para enviar múltiples videos
$urls = @(
    "https://sample-videos.com/zip/10/mp4/mp4/SampleVideo_640x360_1mb.mp4",
    "https://sample-videos.com/zip/10/mp4/mp4/SampleVideo_1280x720_2mb.mp4"
)

foreach ($url in $urls) {
    $body = @{
        video_url = $url
        metadata = @{
            batch_id = [Guid]::NewGuid().ToString()
            timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
        }
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "http://localhost:8080/publish" -Method Post -Body $body -ContentType "application/json"
    Write-Host "Enviado: $url -> Offset $($result.offset)"
    Start-Sleep 1
}
```

## 🔧 Modificaciones y Extensibilidad

### Agregar Nuevo Procesamiento

1. **Extender el Consumer**:
   ```python
   # En consumer.py, agregar nueva lógica en process_message()
   if video_msg.metadata.get("type") == "thumbnail":
       await process_thumbnail(video_msg)
   ```

2. **Actualizar el esquema de metadatos**:
   ```json
   {
     "video_url": "...",
     "metadata": {
       "type": "thumbnail|transcoding|analysis",
       "options": {"resolution": "720p"}
     }
   }
   ```

### Escalar Horizontalmente

```powershell
# Aumentar número de consumers
docker compose up -d --scale consumer=3

# Verificar distribución de particiones
docker compose exec broker1 kafka-consumer-groups --describe --group video-group --bootstrap-server broker1:9092
```

### Agregar Nuevo Servicio

```yaml
# En docker-compose.yml
  nuevo-servicio:
    build: ./nuevo-servicio
    depends_on:
      - broker1
      - broker2
      - broker3
    environment:
      - KAFKA_BOOTSTRAP=broker1:9092,broker2:9092,broker3:9092
    networks:
      - kafka-net
```

### Migrar a Producción

1. **Configurar autenticación SASL**
2. **Habilitar SSL/TLS**
3. **Configurar volúmenes persistentes**
4. **Ajustar recursos y límites**
5. **Implementar monitoreo con Prometheus**

```yaml
# Ejemplo configuración productiva
  broker1:
    environment:
      KAFKA_LISTENERS: SASL_SSL://:9092,CONTROLLER://:9093
      KAFKA_SECURITY_INTER_BROKER_PROTOCOL: SASL_SSL
      KAFKA_SASL_MECHANISM_INTER_BROKER_PROTOCOL: PLAIN
    volumes:
      - /var/kafka-data:/var/lib/kafka/data
      - /etc/kafka/ssl:/etc/kafka/ssl:ro
```

## 🚧 Para Desarrollo Futuro

### Checklist de Modificaciones

- [ ] **Esquemas**: ¿Afecta el formato de mensajes?
- [ ] **API**: ¿Cambian los endpoints o contratos?
- [ ] **Topics**: ¿Se necesitan nuevos topics?
- [ ] **Particiones**: ¿Hay que ajustar el particionado?
- [ ] **Consumer Groups**: ¿Afecta el balanceo de carga?
- [ ] **Backend**: ¿Cambia la integración downstream?
- [ ] **Versionado**: ¿Se mantiene compatibilidad hacia atrás?

### Próximas Mejoras Sugeridas

1. **Schema Registry** para versionado de mensajes
2. **Dead Letter Queue** para mensajes fallidos
3. **Métricas con Prometheus + Grafana**
4. **Autenticación JWT en la API**
5. **Compresión y particionado inteligente**
6. **Tests de integración automatizados**

## ❓ Preguntas Frecuentes

**P: ¿Puedo usar URLs que no sean de Firebase Storage?**
R: Sí, el sistema acepta cualquier URL HTTP/HTTPS válida.

**P: ¿Qué pasa si el backend está caído?**
R: El consumer reintentar con backoff exponencial y activará un circuit breaker tras fallos consecutivos.

**P: ¿Puedo procesar el mismo video múltiples veces?**
R: Sí, cada envío genera un `message_id` único, permitiendo reprocesamiento.

**P: ¿Cómo escalo para más throughput?**
R: Aumenta las particiones del topic y el número de instancias del consumer.

**P: ¿Los datos se persisten si reinicio Docker?**
R: Sí, los volúmenes de Kafka mantienen topics y offsets entre reinicios.

---

**📞 Soporte**: Para problemas o dudas, revisar logs con `docker compose logs [servicio]` y verificar la conectividad de red entre contenedores.