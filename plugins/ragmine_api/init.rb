Redmine::Plugin.register :ragmine_api do
  name 'RAGMine API'
  author 'RAGMine Team'
  description 'REST API endpoints for RAGMine'
  version '0.1.0'
  url 'https://github.com/zacharyelston/ragmine'
  
  # Ensure core plugin is loaded first
  requires_redmine_plugin :ragmine_core, version_or_higher: '0.1.0'
end