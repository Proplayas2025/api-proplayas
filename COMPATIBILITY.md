# Compatibilidad Frontend-Backend Proplayas

## Modelos Actualizados

### User (users)
```python
- id, name, username, email, password
- role: admin | node_leader | member
- status: active | inactive | pending
- about, degree, postgraduate, expertise_area, research_work
- profile_picture, country, city
- node_id (FK)
- Relations: node, led_node, social_links, created_content
```

### Node (nodes)
```python
- id, name, code
- type: comunidad | universidad | organizacion | empresa | institucion
- profile_picture, about, country, city
- ip_address, coordinates, alt_places
- joined_in, members_count, memorandum
- status: active | inactive | pending
- leader_id (FK)
- Relations: leader, members, social_links, memberships
```

### NodeMember (node_members)
```python
- id, user_id (FK), node_id (FK)
- member_code, research_line, work_area
- Relations: user, node
```

### Content (content)
```python
- Base: id, title, description, content_type, status
- type: event | publication | book | project | series
- cover_image, cover_image_url, file_path, file_url, link
- location, created_at, updated_at
- author_id (FK), node_id (FK)

# Eventos
- event_type: event | taller | clase | curso | seminario | foro | conferencia | congreso | webinar
- event_format: presencial | online
- event_date, participants (array)

# Libros
- book_author, publication_date, isbn

# Publicaciones
- publication_type: boletin | guia | articulo
- doi, issn

# Series (Miniseries YouTube)
- Relations: chapters
```

### Chapter (chapters)
```python
- id, title, description
- youtube_url, thumbnail_url, episode_number
- series_id (FK)
```

### SocialLink (social_links)
```python
- id, platform, url, user_id (FK)
- platforms: linkedin | github | twitter | website | facebook | instagram | youtube | research_gate | phone
```

### NodeSocialLink (node_social_links)
```python
- id, platform, url, node_id (FK)
```

### Invitation (invitations)
```python
- id, name, email, token, role, node_type
- status: pending | accepted | expired
- node_id (FK), invited_by (FK)
- created_at, expires_at (7 días)
```

## Endpoints Esperados por Frontend

### Auth
- POST /api/auth/login
- POST /api/auth/register
- POST /api/auth/logout

### Users
- GET /api/users?page=1&per_page=10
- GET /api/user/{id}
- PUT /api/user/{id}
- DELETE /api/user/{id}

### Nodes
- GET /api/nodes?page=1
- GET /api/node/{code}
- GET /api/node/members/{code}
- POST /api/node
- PUT /api/node/{id}

### Content
- GET /api/content?content_type=event&status=published&page=1
- GET /api/content/{id}
- POST /api/content
- PUT /api/content/{id}
- DELETE /api/content/{id}
- PUT /api/content/{id}/toggle-status
- POST /api/content/{id}/upload-file (multipart/form-data)
- POST /api/content/{id}/upload-cover-image (multipart/form-data)

### Invitations
- POST /api/invitations
- POST /api/invitations/validate
- GET /api/invitations

## Respuestas API

Todas las respuestas siguen el formato:
```json
{
  "status": 200,
  "message": "Success message",
  "data": {} | [],
  "meta": {  // Solo en endpoints paginados
    "current_page": 1,
    "per_page": 10,
    "total": 100,
    "last_page": 10
  }
}
```

## Tipos de Contenido por Frontend

### Events
- Necesita: title, type, description, date, link, format, location, participants, cover_image, file

### Projects
- Necesita: title, description, date, location, link, file, cover_image, participants

### Publications
- Necesita: type, title, description, link, doi, issn, cover_image, file

### Books
- Necesita: title, book_author, publication_date, isbn, description, link, file, cover_image

### Series (Miniseries)
- Necesita: title, url, description, cover_image
- Chapters: title, description, youtube_url, thumbnail_url, episode_number

## Relaciones Frontend-Backend

TypeScript Interface → Python Model:
- `Profile.User` → `models.user.User`
- `Nodes.Node` → `models.node.Node`
- `Nodes.NodeMembers` → `models.node_member.NodeMember`
- `Content.Events` → `models.content.Content` (content_type=event)
- `Content.Projects` → `models.content.Content` (content_type=project)
- `Content.Publications` → `models.content.Content` (content_type=publication)
- `Content.Books` → `models.content.Content` (content_type=book)
- `Content.Series` → `models.content.Content` (content_type=series)
- `Invitations.*` → `models.invitation.Invitation`
