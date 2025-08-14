# Ragmine - AI-Powered Search for Redmine/RedMica

Ragmine adds advanced RAG (Retrieval-Augmented Generation) capabilities to Redmine and RedMica, providing intelligent, context-aware search functionality powered by modern AI technologies.

## Features

- 🔍 **Semantic Search**: Understand the meaning behind queries, not just keywords
- 🤖 **AI-Powered Results**: Get intelligent summaries and relevant answers
- ⚡ **Smart Caching**: Lightning-fast responses for common queries
- 📊 **Analytics Dashboard**: Track search usage and performance
- 🔄 **Automatic Indexing**: Keep search index up-to-date automatically
- 🛡️ **Graceful Fallback**: Falls back to basic search if AI service is unavailable
- 🌍 **Multi-language Support**: Extensible localization system

## Architecture

Ragmine uses a client-server architecture:
- **Plugin (Ruby)**: Lightweight client integrated with Redmine
- **RAG Service (Python)**: External service handling AI operations
- **Vector Database**: Stores document embeddings for semantic search

## Requirements

### Redmine/RedMica Plugin
- Redmine >= 4.0.0 or RedMica >= 2.0.0
- Ruby >= 2.7.0
- Rails >= 5.2.0
- Redis (for caching and job queue)

### RAG Service
- Python >= 3.10
- FastAPI
- LangChain
- Vector database (Qdrant, Chroma, or Pinecone)

## Installation

### 1. Install the Plugin

```bash
# Navigate to your Redmine plugins directory
cd /path/to/redmine/plugins

# Clone the repository
git clone https://github.com/yourusername/ragmine.git

# Install dependencies
cd ragmine
bundle install

# Run migrations
cd ../..
bundle exec rake redmine:plugins:migrate RAILS_ENV=production

# Restart Redmine
# (method depends on your deployment)
```

### 2. Deploy the RAG Service

```bash
# Navigate to RAG service directory
cd plugins/ragmine/rag_service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run the service
uvicorn app:app --host 0.0.0.0 --port 8000
```

### 3. Configure the Plugin

1. Go to **Administration > Plugins > Ragmine > Configure**
2. Set the RAG Service URL (e.g., `http://localhost:8000`)
3. Configure API keys if using external services
4. Test the connection
5. Save settings

### 4. Enable for Projects

1. Go to **Project > Settings > Modules**
2. Enable "AI-Powered Search"
3. Configure project-specific permissions in **Project > Settings > Members**

## Quick Start

### Using Docker Compose

```bash
# Clone the repository
git clone https://github.com/yourusername/ragmine.git
cd ragmine

# Start all services
docker-compose up -d

# Run initial indexing
docker-compose exec redmine bundle exec rake ragmine:index_all
```

### Manual Setup

1. **Configure Settings**: Admin > Plugins > Ragmine > Configure
2. **Test Connection**: Click "Test Connection" button
3. **Initial Indexing**: Run `bundle exec rake ragmine:index_all`
4. **Enable for Projects**: Project Settings > Modules > AI-Powered Search

## Configuration

### Plugin Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `service_url` | RAG Service endpoint | `http://localhost:8000` |
| `api_key` | API key for service authentication | - |
| `timeout` | Request timeout in seconds | `30` |
| `enable_cache` | Enable result caching | `true` |
| `cache_ttl` | Cache time-to-live in seconds | `300` |
| `fallback_mode` | Behavior when service is down | `basic` |
| `max_results` | Maximum search results | `20` |

### Environment Variables

```bash
# RAG Service
OPENAI_API_KEY=your-openai-key
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-3.5-turbo
VECTOR_DB_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
```

## Usage

### Basic Search

1. Navigate to any project with Ragmine enabled
2. Click on "AI Search" in the project menu
3. Enter your query in natural language
4. Toggle "Use AI-powered search" for semantic search
5. View results with AI-generated summaries

### Advanced Features

- **Query Suggestions**: Start typing for intelligent suggestions
- **Filters**: Narrow results by type, date, status
- **Feedback**: Help improve results by providing feedback
- **Analytics**: View search metrics in the admin panel

## Development

### Running Tests

```bash
# Plugin tests
RAILS_ENV=test bundle exec rake redmine:plugins:test NAME=ragmine

# Service tests
cd rag_service
pytest tests/
```

### Development Mode

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up

# Watch for changes
./bin/dev
```

## API Documentation

### Search Endpoint

```http
POST /api/v1/search
Content-Type: application/json

{
  "query": "How to create custom fields?",
  "project_id": 1,
  "limit": 10,
  "search_type": "hybrid"
}
```

### Index Endpoint

```http
POST /api/v1/index
Content-Type: application/json

{
  "document_type": "Issue",
  "document_id": "123",
  "content": "Issue content...",
  "metadata": {
    "project_id": 1,
    "status": "open"
  }
}
```

## Troubleshooting

### Service Connection Issues

1. Check service is running: `curl http://localhost:8000/health`
2. Verify firewall settings
3. Check Redis connectivity
4. Review service logs: `docker-compose logs rag-service`

### Indexing Problems

1. Check background jobs: Admin > Background Jobs
2. Verify permissions for indexing
3. Run manual reindex: `bundle exec rake ragmine:reindex`

### Performance Issues

1. Enable caching in settings
2. Increase cache TTL for stable content
3. Check vector database performance
4. Monitor with analytics dashboard

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Roadmap

- [ ] Support for additional LLM providers (Anthropic, Cohere, local models)
- [ ] Advanced query transformations (HyDE, multi-query)
- [ ] Real-time indexing with webhooks
- [ ] Export search analytics
- [ ] Multi-language query support
- [ ] Fine-tuning support for domain-specific models

## Support

- **Documentation**: [https://ragmine.docs.com](https://ragmine.docs.com)
- **Issues**: [GitHub Issues](https://github.com/yourusername/ragmine/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ragmine/discussions)
- **Email**: support@ragmine.com

## License

This plugin is licensed under the GNU General Public License v2.0. See [LICENSE](LICENSE) file for details.

## Acknowledgments

- Redmine/RedMica development teams
- LangChain community
- OpenAI for API services
- All contributors and testers

## Changelog

### Version 0.1.0 (2024-01-01)
- Initial release
- Basic semantic search
- Document indexing
- Settings UI
- Analytics dashboard

---

Made with ❤️ for the Redmine community
