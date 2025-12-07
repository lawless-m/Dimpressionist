# API Specification

RESTful API and WebSocket interface for the Conversational Image Generator.

---

## Base Configuration

```
Base URL: http://localhost:8000
WebSocket: ws://localhost:8000/ws
API Version: v1
Content-Type: application/json
```

---

## Authentication

**Current:** None (local-only deployment)

**Future:** JWT tokens for multi-user deployment
```
Authorization: Bearer <token>
```

---

## REST Endpoints

### 1. Generation Endpoints

#### POST /api/v1/generate/new
Generate a new image from text prompt.

**Request:**
```json
{
  "prompt": "a blue ball on green grass",
  "steps": 28,
  "guidance_scale": 3.5,
  "seed": 42,
  "width": 1024,
  "height": 1024
}
```

**Required Fields:**
- `prompt` (string, 1-500 chars)

**Optional Fields:**
- `steps` (integer, 10-100, default: 28)
- `guidance_scale` (float, 1.0-5.0, default: 3.5)
- `seed` (integer, null for random, default: null)
- `width` (integer, 512-2048, default: 1024)
- `height` (integer, 512-2048, default: 1024)

**Response (200 OK):**
```json
{
  "id": "gen_001_20241207_143022",
  "image_url": "/api/v1/images/gen_001_20241207_143022.png",
  "metadata": {
    "prompt": "a blue ball on green grass",
    "seed": 42,
    "steps": 28,
    "guidance_scale": 3.5,
    "width": 1024,
    "height": 1024,
    "generation_time": 18.5,
    "timestamp": "2024-12-07T14:30:22Z"
  }
}
```

**Errors:**
- `400 Bad Request` - Invalid parameters
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Generation failed

---

#### POST /api/v1/generate/refine
Refine current image with modification.

**Request:**
```json
{
  "modification": "make the ball red",
  "strength": 0.6,
  "steps": 28,
  "guidance_scale": 3.5
}
```

**Required Fields:**
- `modification` (string, 1-500 chars)

**Optional Fields:**
- `strength` (float, 0.1-1.0, default: 0.6)
- `steps` (integer, 10-100, default: 28)
- `guidance_scale` (float, 1.0-5.0, default: 3.5)

**Response (200 OK):**
```json
{
  "id": "gen_002_20241207_143045_refined",
  "image_url": "/api/v1/images/gen_002_20241207_143045_refined.png",
  "metadata": {
    "modification": "make the ball red",
    "new_prompt": "a red ball on green grass",
    "parent_id": "gen_001_20241207_143022",
    "strength": 0.6,
    "seed": 42,
    "steps": 28,
    "guidance_scale": 3.5,
    "generation_time": 15.2,
    "timestamp": "2024-12-07T14:30:45Z"
  }
}
```

**Errors:**
- `400 Bad Request` - No current image or invalid params
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Refinement failed

---

#### POST /api/v1/generate/cancel
Cancel ongoing generation.

**Request:** Empty body

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Generation cancelled"
}
```

**Errors:**
- `404 Not Found` - No active generation

---

### 2. Session Endpoints

#### GET /api/v1/session/current
Get current session state.

**Response (200 OK):**
```json
{
  "session_id": "sess_abc123",
  "current_image": {
    "id": "gen_002_20241207_143045_refined",
    "url": "/api/v1/images/gen_002_20241207_143045_refined.png",
    "prompt": "a red ball on green grass",
    "seed": 42
  },
  "generation_count": 2,
  "created_at": "2024-12-07T14:25:00Z",
  "updated_at": "2024-12-07T14:30:45Z"
}
```

**Empty Session:**
```json
{
  "session_id": "sess_abc123",
  "current_image": null,
  "generation_count": 0,
  "created_at": "2024-12-07T14:25:00Z",
  "updated_at": "2024-12-07T14:25:00Z"
}
```

---

#### GET /api/v1/session/history
Get generation history.

**Query Parameters:**
- `limit` (integer, 1-100, default: 50)
- `offset` (integer, default: 0)
- `type` (string, "all" | "new" | "refinement", default: "all")

**Response (200 OK):**
```json
{
  "total": 45,
  "limit": 50,
  "offset": 0,
  "generations": [
    {
      "id": "gen_002_20241207_143045_refined",
      "type": "refinement",
      "image_url": "/api/v1/images/gen_002_20241207_143045_refined.png",
      "thumbnail_url": "/api/v1/thumbnails/gen_002_20241207_143045_refined.jpg",
      "prompt": "a red ball on green grass",
      "modification": "make the ball red",
      "parent_id": "gen_001_20241207_143022",
      "timestamp": "2024-12-07T14:30:45Z",
      "metadata": {
        "seed": 42,
        "steps": 28,
        "strength": 0.6
      }
    },
    {
      "id": "gen_001_20241207_143022",
      "type": "new",
      "image_url": "/api/v1/images/gen_001_20241207_143022.png",
      "thumbnail_url": "/api/v1/thumbnails/gen_001_20241207_143022.jpg",
      "prompt": "a blue ball on green grass",
      "parent_id": null,
      "timestamp": "2024-12-07T14:30:22Z",
      "metadata": {
        "seed": 42,
        "steps": 28
      }
    }
  ]
}
```

---

#### POST /api/v1/session/clear
Clear current session.

**Request:** Empty body

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Session cleared",
  "images_deleted": 45
}
```

---

#### GET /api/v1/session/export
Export session as JSON.

**Response (200 OK):**
```json
{
  "session_id": "sess_abc123",
  "exported_at": "2024-12-07T15:00:00Z",
  "generations": [
    // Full generation history with metadata
  ]
}
```

**Alternative:** Download as file
```
Content-Type: application/json
Content-Disposition: attachment; filename="session_sess_abc123.json"
```

---

### 3. Image Endpoints

#### GET /api/v1/images/{image_id}
Get full-resolution image.

**Response (200 OK):**
```
Content-Type: image/png
Content-Length: 1234567
[Binary image data]
```

**Errors:**
- `404 Not Found` - Image doesn't exist

---

#### GET /api/v1/thumbnails/{image_id}
Get thumbnail (120x120 JPEG).

**Response (200 OK):**
```
Content-Type: image/jpeg
Content-Length: 12345
[Binary image data]
```

---

#### DELETE /api/v1/images/{image_id}
Delete a specific image.

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Image deleted"
}
```

**Errors:**
- `404 Not Found` - Image doesn't exist
- `409 Conflict` - Cannot delete current image

---

### 4. Configuration Endpoints

#### GET /api/v1/config
Get current configuration.

**Response (200 OK):**
```json
{
  "model": "FLUX.1-dev",
  "default_parameters": {
    "steps": 28,
    "guidance_scale": 3.5,
    "strength": 0.6
  },
  "limits": {
    "max_steps": 100,
    "max_width": 2048,
    "max_height": 2048
  },
  "features": {
    "refinement": true,
    "inpainting": false,
    "batch_generation": false
  }
}
```

---

#### POST /api/v1/config
Update configuration.

**Request:**
```json
{
  "default_parameters": {
    "steps": 30,
    "guidance_scale": 4.0
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Configuration updated"
}
```

---

### 5. System Endpoints

#### GET /api/v1/system/status
Get system health and status.

**Response (200 OK):**
```json
{
  "status": "operational",
  "model_loaded": true,
  "gpu_info": {
    "name": "NVIDIA RTX 3090",
    "memory_total": 24564,
    "memory_used": 12280,
    "memory_free": 12284,
    "utilization": 45
  },
  "queue": {
    "active": 0,
    "pending": 0
  },
  "uptime": 3600,
  "version": "1.0.0"
}
```

---

#### GET /api/v1/system/stats
Get usage statistics.

**Response (200 OK):**
```json
{
  "total_generations": 245,
  "total_refinements": 189,
  "total_images": 434,
  "avg_generation_time": 18.5,
  "avg_refinement_time": 14.2,
  "disk_usage": {
    "total": 50000,
    "used": 12345,
    "free": 37655
  },
  "session_stats": {
    "current_session_count": 12,
    "avg_generations_per_session": 8.5
  }
}
```

---

## WebSocket Interface

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws');
```

### Client → Server Messages

#### Subscribe to Progress
```json
{
  "type": "subscribe",
  "channel": "generation_progress"
}
```

#### Unsubscribe
```json
{
  "type": "unsubscribe",
  "channel": "generation_progress"
}
```

#### Ping (keep-alive)
```json
{
  "type": "ping"
}
```

### Server → Client Messages

#### Progress Update
```json
{
  "type": "progress",
  "generation_id": "gen_003_20241207_143100",
  "data": {
    "step": 15,
    "total_steps": 28,
    "percentage": 53.57,
    "eta_seconds": 8.5,
    "status": "generating"
  }
}
```

#### Generation Complete
```json
{
  "type": "complete",
  "generation_id": "gen_003_20241207_143100",
  "data": {
    "image_url": "/api/v1/images/gen_003_20241207_143100.png",
    "metadata": {
      "generation_time": 18.5
    }
  }
}
```

#### Error
```json
{
  "type": "error",
  "generation_id": "gen_003_20241207_143100",
  "error": {
    "code": "GENERATION_FAILED",
    "message": "Out of memory",
    "details": "Reduce image size or steps"
  }
}
```

#### Pong (response to ping)
```json
{
  "type": "pong"
}
```

#### Session Update (when history changes)
```json
{
  "type": "session_update",
  "data": {
    "generation_count": 13,
    "current_image_id": "gen_003_20241207_143100"
  }
}
```

---

## Error Response Format

All error responses follow this structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": "Additional information",
    "timestamp": "2024-12-07T14:30:45Z"
  }
}
```

### Error Codes

**Client Errors (4xx):**
- `INVALID_REQUEST` - Malformed request
- `INVALID_PARAMETERS` - Parameter validation failed
- `NO_CURRENT_IMAGE` - Cannot refine without current image
- `IMAGE_NOT_FOUND` - Requested image doesn't exist
- `RATE_LIMIT_EXCEEDED` - Too many requests

**Server Errors (5xx):**
- `MODEL_NOT_LOADED` - ML model failed to load
- `GENERATION_FAILED` - Image generation error
- `OUT_OF_MEMORY` - Insufficient GPU memory
- `INTERNAL_ERROR` - Unexpected server error

---

## Rate Limiting

**Limits:**
- 10 generations per minute (burst: 3)
- 60 API calls per minute (burst: 10)
- WebSocket: 1 connection per client

**Headers:**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1701960000
```

**Response (429):**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "retry_after": 30
  }
}
```

---

## Caching Headers

### Images (immutable)
```
Cache-Control: public, max-age=31536000, immutable
ETag: "abc123..."
```

### API Responses (short-lived)
```
Cache-Control: private, max-age=60
ETag: "xyz789..."
```

---

## CORS Configuration

**Development:**
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

**Production:**
```
Access-Control-Allow-Origin: https://yourdomain.com
Access-Control-Allow-Credentials: true
```

---

## Webhooks (Future)

For external integrations:

```json
{
  "url": "https://external-service.com/webhook",
  "events": ["generation.complete", "generation.failed"],
  "secret": "webhook_secret_key"
}
```

Payload:
```json
{
  "event": "generation.complete",
  "timestamp": "2024-12-07T14:30:45Z",
  "data": {
    "generation_id": "gen_003_20241207_143100",
    "image_url": "http://localhost:8000/api/v1/images/..."
  },
  "signature": "sha256=..."
}
```

---

## API Client Examples

### JavaScript (Fetch)
```javascript
// Generate new image
async function generateImage(prompt) {
  const response = await fetch('http://localhost:8000/api/v1/generate/new', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, steps: 28 })
  });
  return await response.json();
}

// WebSocket progress
const ws = new WebSocket('ws://localhost:8000/api/v1/ws');
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'progress') {
    console.log(`Progress: ${message.data.percentage}%`);
  }
};
```

### Python (Requests)
```python
import requests

# Generate new image
def generate_image(prompt: str):
    response = requests.post(
        'http://localhost:8000/api/v1/generate/new',
        json={'prompt': prompt, 'steps': 28}
    )
    return response.json()

# Get session history
def get_history():
    response = requests.get(
        'http://localhost:8000/api/v1/session/history',
        params={'limit': 20}
    )
    return response.json()
```

### cURL
```bash
# Generate new image
curl -X POST http://localhost:8000/api/v1/generate/new \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a cat", "steps": 28}'

# Refine current image
curl -X POST http://localhost:8000/api/v1/generate/refine \
  -H "Content-Type: application/json" \
  -d '{"modification": "make it blue", "strength": 0.6}'

# Get session history
curl http://localhost:8000/api/v1/session/history?limit=10
```

---

## Versioning

API versions specified in URL path: `/api/v1/...`

**Deprecation Policy:**
- New version: Announce 3 months prior
- Old version: Supported for 6 months after new version
- Breaking changes: Only in major versions

**Version Header (optional):**
```
X-API-Version: 1.0.0
```

---

## Performance Expectations

**API Response Times (excluding generation):**
- Simple GET: < 50ms
- POST with validation: < 100ms
- Image serving: < 200ms
- WebSocket messages: < 10ms latency

**Generation Times (RTX 3090):**
- New image (28 steps): 15-30s
- Refinement (28 steps): 12-25s
- Progress updates: Every 500ms

---

## Security Considerations

### Input Validation
- Sanitize all user input
- Validate prompt length (max 500 chars)
- Check parameter ranges
- Prevent path traversal in image requests

### Resource Protection
- Rate limiting per IP
- Maximum request size (10MB)
- Timeout for long operations (5min)
- Queue size limits

### Data Privacy
- Images stored locally
- No cloud uploads
- Optional session encryption
- Secure WebSocket (WSS in production)

---

## Testing

### Unit Tests
- Endpoint validation
- Parameter checking
- Error handling
- Response formatting

### Integration Tests
- Full generation workflow
- WebSocket communication
- Session persistence
- Concurrent requests

### Load Tests
- 10 concurrent generations
- 100 API requests/second
- WebSocket stability
- Memory leak detection

---

## Monitoring & Logging

### Metrics to Track
- Request count per endpoint
- Response times (p50, p95, p99)
- Generation success/failure rate
- GPU utilization
- Memory usage
- Disk usage

### Logging Format
```json
{
  "timestamp": "2024-12-07T14:30:45Z",
  "level": "INFO",
  "endpoint": "/api/v1/generate/new",
  "method": "POST",
  "status": 200,
  "duration": 18500,
  "user_agent": "Mozilla/5.0..."
}
```

---

**Document Version:** 1.0  
**Last Updated:** December 2025  
**For:** Claude Code implementation
