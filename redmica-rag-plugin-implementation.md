# RedMica RAG Plugin - Practical Implementation Guide

Following the official Redmine Plugin Tutorial structure, this guide provides a step-by-step implementation of RAG capabilities for RedMica.

## Step 1: Generate the Plugin Structure

```bash
# From your redmica root directory
bundle exec rails generate redmine_plugin RedmineRag
```

This creates the standard plugin structure:
```
plugins/redmine_rag/
├── app/
│   ├── controllers/
│   ├── helpers/
│   ├── models/
│   └── views/
├── assets/
│   ├── images/
│   ├── javascripts/
│   └── stylesheets/
├── config/
│   ├── locales/
│   │   └── en.yml
│   └── routes.rb
├── db/
│   └── migrate/
├── lib/
│   └── tasks/
├── test/
├── init.rb
└── README.rdoc
```

## Step 2: Configure Plugin Registration

### plugins/redmine_rag/init.rb

```ruby
require_dependency File.expand_path('../lib/redmine_rag/hooks', __FILE__)
require_dependency File.expand_path('../lib/redmine_rag/patches/issue_patch', __FILE__)
require_dependency File.expand_path('../lib/redmine_rag/patches/wiki_page_patch', __FILE__)

Redmine::Plugin.register :redmine_rag do
  name 'Redmine RAG plugin'
  author 'Your Organization'
  description 'Adds RAG (Retrieval-Augmented Generation) capabilities to Redmine search'
  version '0.1.0'
  url 'http://example.com/redmine_rag'
  author_url 'http://example.com'
  
  # Add permissions
  project_module :rag_search do
    permission :use_rag_search, { rag_search: [:index, :search, :suggestions] }
    permission :manage_rag_index, { rag_admin: [:index, :reindex, :settings] }
  end
  
  # Add menu items
  menu :project_menu, :rag_search, 
       { controller: 'rag_search', action: 'index' }, 
       caption: 'AI Search',
       after: :issues,
       param: :project_id,
       if: Proc.new { |project| project.enabled_module_names.include?('rag_search') }
       
  menu :admin_menu, :rag_settings,
       { controller: 'rag_admin', action: 'index' },
       caption: 'RAG Settings',
       after: :settings
       
  # Plugin settings
  settings default: {
    'api_provider' => 'openai',
    'embedding_model' => 'text-embedding-ada-002',
    'llm_model' => 'gpt-3.5-turbo',
    'chunk_size' => '500',
    'chunk_overlap' => '50',
    'use_hyde' => false,
    'use_multiquery' => true,
    'python_service_url' => 'http://localhost:8000'
  }, partial: 'settings/rag_settings'
end
```

## Step 3: Generate Models

```bash
# Generate the RAG document model
bundle exec rails generate redmine_plugin_model redmine_rag rag_document \
  source_type:string source_id:integer vector_id:string \
  content:text metadata:text indexed_at:datetime

# Generate the RAG query log model  
bundle exec rails generate redmine_plugin_model redmine_rag rag_query \
  user_id:integer query:text transformed_queries:text \
  results_count:integer response_time:float
```

### plugins/redmine_rag/app/models/rag_document.rb

```ruby
class RagDocument < ActiveRecord::Base
  # Associations
  belongs_to :project, optional: true
  belongs_to :user, optional: true
  
  # Validations
  validates :source_type, presence: true
  validates :source_id, presence: true
  
  # Scopes
  scope :indexed, -> { where.not(indexed_at: nil) }
  scope :for_project, ->(project) { where(project_id: project.id) }
  
  # Serialize metadata
  serialize :metadata, Hash
  
  class << self
    def index_issue(issue)
      doc = find_or_initialize_by(
        source_type: 'Issue',
        source_id: issue.id
      )
      
      doc.content = build_issue_content(issue)
      doc.metadata = {
        project_id: issue.project_id,
        tracker: issue.tracker.name,
        status: issue.status.name,
        author: issue.author.name,
        assigned_to: issue.assigned_to&.name,
        created_at: issue.created_at,
        updated_at: issue.updated_at
      }
      doc.project_id = issue.project_id
      
      # Send to Python service for embedding
      if doc.save
        RagIndexingJob.perform_later(doc)
      end
      
      doc
    end
    
    def index_wiki_page(wiki_page)
      doc = find_or_initialize_by(
        source_type: 'WikiPage',
        source_id: wiki_page.id
      )
      
      doc.content = build_wiki_content(wiki_page)
      doc.metadata = {
        project_id: wiki_page.wiki.project_id,
        title: wiki_page.title,
        version: wiki_page.version,
        author: wiki_page.content.author.name,
        updated_at: wiki_page.updated_on
      }
      doc.project_id = wiki_page.wiki.project_id
      
      if doc.save
        RagIndexingJob.perform_later(doc)
      end
      
      doc
    end
    
    private
    
    def build_issue_content(issue)
      parts = []
      parts << "Title: #{issue.subject}"
      parts << "Description: #{issue.description}" if issue.description.present?
      
      # Include journal notes
      issue.journals.each do |journal|
        next if journal.notes.blank?
        parts << "Comment by #{journal.user.name}: #{journal.notes}"
      end
      
      # Include attachment names
      if issue.attachments.any?
        parts << "Attachments: #{issue.attachments.map(&:filename).join(', ')}"
      end
      
      parts.join("\n\n")
    end
    
    def build_wiki_content(wiki_page)
      parts = []
      parts << "Title: #{wiki_page.title}"
      parts << wiki_page.content.text
      parts.join("\n\n")
    end
  end
end
```

## Step 4: Generate Controllers

```bash
bundle exec rails generate redmine_plugin_controller redmine_rag rag_search \
  index search suggestions
  
bundle exec rails generate redmine_plugin_controller redmine_rag rag_admin \
  index reindex settings
```

### plugins/redmine_rag/app/controllers/rag_search_controller.rb

```ruby
class RagSearchController < ApplicationController
  before_action :find_project, :authorize
  
  def index
    @query = params[:q] || ""
    @use_rag = params[:use_rag] == '1'
    
    if @query.present? && @use_rag
      perform_rag_search
    elsif @query.present?
      perform_standard_search
    end
  end
  
  def search
    @query = params[:q]
    @results = []
    
    if @query.present?
      # Log the query
      query_log = RagQuery.create!(
        user_id: User.current.id,
        query: @query,
        project_id: @project&.id
      )
      
      start_time = Time.current
      
      # Call Python RAG service
      rag_results = RagService.new(@project).search(@query, {
        use_hyde: Setting.plugin_redmine_rag['use_hyde'],
        use_multiquery: Setting.plugin_redmine_rag['use_multiquery']
      })
      
      # Process results
      @results = process_rag_results(rag_results)
      
      # Update query log
      query_log.update!(
        results_count: @results.size,
        response_time: Time.current - start_time,
        transformed_queries: rag_results[:transformed_queries]
      )
    end
    
    respond_to do |format|
      format.html { render :index }
      format.json { render json: @results }
    end
  end
  
  def suggestions
    @query = params[:q]
    suggestions = []
    
    if @query.present? && @query.length >= 3
      # Get query suggestions from RAG service
      suggestions = RagService.new(@project).get_suggestions(@query)
    end
    
    render json: suggestions
  end
  
  private
  
  def find_project
    @project = Project.find(params[:project_id]) if params[:project_id]
  end
  
  def perform_rag_search
    service = RagService.new(@project)
    @rag_results = service.search(@query)
    @results = process_rag_results(@rag_results)
  end
  
  def perform_standard_search
    # Fallback to standard Redmine search
    @results = Issue.visible.where(
      "subject LIKE ? OR description LIKE ?", 
      "%#{@query}%", 
      "%#{@query}%"
    ).limit(20)
  end
  
  def process_rag_results(rag_results)
    results = []
    
    rag_results[:documents].each do |doc|
      case doc[:source_type]
      when 'Issue'
        issue = Issue.find_by(id: doc[:source_id])
        if issue && issue.visible?
          results << {
            type: 'Issue',
            title: issue.subject,
            url: issue_path(issue),
            project: issue.project.name,
            updated_at: issue.updated_on,
            snippet: doc[:snippet],
            relevance_score: doc[:score],
            ai_summary: doc[:ai_summary]
          }
        end
      when 'WikiPage'
        wiki_page = WikiPage.find_by(id: doc[:source_id])
        if wiki_page && User.current.allowed_to?(:view_wiki_pages, wiki_page.wiki.project)
          results << {
            type: 'Wiki',
            title: wiki_page.title,
            url: project_wiki_page_path(wiki_page.wiki.project, wiki_page),
            project: wiki_page.wiki.project.name,
            updated_at: wiki_page.updated_on,
            snippet: doc[:snippet],
            relevance_score: doc[:score],
            ai_summary: doc[:ai_summary]
          }
        end
      end
    end
    
    results
  end
end
```

## Step 5: Create Views

### plugins/redmine_rag/app/views/rag_search/index.html.erb

```erb
<h2>AI-Powered Search</h2>

<%= form_tag search_project_rag_search_path(@project), method: :get, id: 'rag-search-form' do %>
  <div class="box">
    <p>
      <%= text_field_tag 'q', @query, 
          size: 60, 
          id: 'rag-search-input',
          placeholder: 'Ask a question or search...',
          class: 'autocomplete' %>
      <%= submit_tag l(:button_search) %>
    </p>
    
    <p>
      <%= check_box_tag 'use_rag', '1', params[:use_rag] == '1' %>
      <%= label_tag 'use_rag', 'Use AI-powered search' %>
      
      <span class="rag-options" style="<%= params[:use_rag] == '1' ? '' : 'display:none;' %>">
        | 
        <%= check_box_tag 'use_hyde', '1', params[:use_hyde] == '1' %>
        <%= label_tag 'use_hyde', 'HyDE' %>
        
        <%= check_box_tag 'use_multiquery', '1', params[:use_multiquery] == '1' %>
        <%= label_tag 'use_multiquery', 'Multi-Query' %>
      </span>
    </p>
  </div>
<% end %>

<% if @results.present? %>
  <h3>Search Results (<%= @results.size %>)</h3>
  
  <% @results.each do |result| %>
    <div class="rag-result">
      <h4>
        <%= link_to result[:title], result[:url], class: result[:type].downcase %>
        <% if result[:relevance_score] %>
          <span class="relevance-score" title="Relevance: <%= result[:relevance_score] %>">
            <%= "★" * [(result[:relevance_score] * 5).round, 5].min %>
          </span>
        <% end %>
      </h4>
      
      <p class="metadata">
        <%= result[:type] %> - 
        <%= result[:project] %> - 
        <%= time_ago_in_words(result[:updated_at]) %> ago
      </p>
      
      <div class="snippet">
        <%= highlight(result[:snippet], @query.split, highlighter: '<mark>\1</mark>') %>
      </div>
      
      <% if result[:ai_summary].present? %>
        <div class="ai-summary">
          <strong>AI Summary:</strong> <%= result[:ai_summary] %>
        </div>
      <% end %>
    </div>
  <% end %>
<% end %>

<%= javascript_tag do %>
  $(function() {
    $('#use_rag').change(function() {
      $('.rag-options').toggle(this.checked);
    });
    
    // Autocomplete for search suggestions
    $('#rag-search-input').autocomplete({
      source: function(request, response) {
        $.ajax({
          url: '<%= suggestions_project_rag_search_path(@project, format: :json) %>',
          data: { q: request.term },
          success: function(data) {
            response(data);
          }
        });
      },
      minLength: 3
    });
  });
<% end %>

<% content_for :header_tags do %>
  <%= stylesheet_link_tag 'rag_search', plugin: 'redmine_rag' %>
<% end %>
```

## Step 6: Add Routes

### plugins/redmine_rag/config/routes.rb

```ruby
# Project routes
resources :projects do
  resources :rag_search, only: [:index] do
    collection do
      get 'search'
      get 'suggestions'
    end
  end
end

# Admin routes
namespace :admin do
  resources :rag_settings, only: [:index] do
    collection do
      post 'reindex'
      post 'clear_index'
    end
  end
end
```

## Step 7: Create Service Layer

### plugins/redmine_rag/lib/redmine_rag/rag_service.rb

```ruby
require 'net/http'
require 'json'

module RedmineRag
  class RagService
    attr_reader :project
    
    def initialize(project = nil)
      @project = project
      @base_url = Setting.plugin_redmine_rag['python_service_url']
    end
    
    def search(query, options = {})
      # Build request
      request_data = {
        query: query,
        project_id: @project&.id,
        user_id: User.current.id,
        options: {
          use_hyde: options[:use_hyde] || false,
          use_multiquery: options[:use_multiquery] || false,
          top_k: options[:top_k] || 10
        }
      }
      
      # Call Python service
      response = post_request('/search', request_data)
      
      # Parse response
      if response.code == '200'
        JSON.parse(response.body, symbolize_names: true)
      else
        Rails.logger.error "RAG Service error: #{response.code} - #{response.body}"
        { documents: [], error: "Search service unavailable" }
      end
    end
    
    def index_document(rag_document)
      request_data = {
        id: "#{rag_document.source_type}_#{rag_document.source_id}",
        content: rag_document.content,
        metadata: rag_document.metadata
      }
      
      response = post_request('/index', request_data)
      
      if response.code == '200'
        result = JSON.parse(response.body)
        rag_document.update!(
          vector_id: result['vector_id'],
          indexed_at: Time.current
        )
        true
      else
        Rails.logger.error "Indexing error: #{response.body}"
        false
      end
    end
    
    def get_suggestions(query)
      response = get_request('/suggestions', { q: query })
      
      if response.code == '200'
        JSON.parse(response.body)
      else
        []
      end
    end
    
    private
    
    def post_request(endpoint, data)
      uri = URI("#{@base_url}#{endpoint}")
      http = Net::HTTP.new(uri.host, uri.port)
      http.read_timeout = 30
      
      request = Net::HTTP::Post.new(uri)
      request['Content-Type'] = 'application/json'
      request.body = data.to_json
      
      http.request(request)
    end
    
    def get_request(endpoint, params = {})
      uri = URI("#{@base_url}#{endpoint}")
      uri.query = URI.encode_www_form(params) if params.any?
      
      Net::HTTP.get_response(uri)
    end
  end
end
```

## Step 8: Create Background Jobs

### plugins/redmine_rag/app/jobs/rag_indexing_job.rb

```ruby
class RagIndexingJob < ApplicationJob
  queue_as :default
  
  def perform(rag_document)
    service = RedmineRag::RagService.new
    service.index_document(rag_document)
  end
end
```

## Step 9: Add Hooks

### plugins/redmine_rag/lib/redmine_rag/hooks.rb

```ruby
module RedmineRag
  class Hooks < Redmine::Hook::ViewListener
    # Add RAG search box to project overview
    render_on :view_projects_show_left, partial: "hooks/project_rag_search"
    
    # Add indexing status to issues
    render_on :view_issues_show_description_bottom, partial: "hooks/issue_rag_status"
    
    # Hook into issue save to trigger indexing
    def controller_issues_new_after_save(context = {})
      issue = context[:issue]
      RagDocument.index_issue(issue) if issue.project.module_enabled?('rag_search')
    end
    
    def controller_issues_edit_after_save(context = {})
      issue = context[:issue]
      RagDocument.index_issue(issue) if issue.project.module_enabled?('rag_search')
    end
    
    # Hook into wiki save
    def controller_wiki_edit_after_save(context = {})
      page = context[:page]
      if page.wiki.project.module_enabled?('rag_search')
        RagDocument.index_wiki_page(page)
      end
    end
  end
end
```

## Step 10: Add Patches

### plugins/redmine_rag/lib/redmine_rag/patches/issue_patch.rb

```ruby
module RedmineRag
  module Patches
    module IssuePatch
      def self.included(base)
        base.class_eval do
          has_one :rag_document, 
                  -> { where(source_type: 'Issue') },
                  foreign_key: :source_id,
                  dependent: :destroy
          
          after_commit :update_rag_index, if: :saved_changes?
          
          def update_rag_index
            if project.module_enabled?('rag_search')
              RagDocument.index_issue(self)
            end
          end
          
          def rag_indexed?
            rag_document&.indexed_at.present?
          end
        end
      end
    end
  end
end

# Apply patch
Rails.configuration.to_prepare do
  unless Issue.included_modules.include?(RedmineRag::Patches::IssuePatch)
    Issue.include(RedmineRag::Patches::IssuePatch)
  end
end
```

## Step 11: Settings View

### plugins/redmine_rag/app/views/settings/_rag_settings.html.erb

```erb
<table>
  <tbody>
    <tr>
      <th>Python Service URL</th>
      <td>
        <%= text_field_tag 'settings[python_service_url]', 
            settings['python_service_url'], 
            size: 60 %>
        <em class="info">URL of the Python RAG service</em>
      </td>
    </tr>
    
    <tr>
      <th>API Provider</th>
      <td>
        <%= select_tag 'settings[api_provider]',
            options_for_select([
              ['OpenAI', 'openai'],
              ['Anthropic', 'anthropic'],
              ['Local LLM', 'local']
            ], settings['api_provider']) %>
      </td>
    </tr>
    
    <tr>
      <th>Embedding Model</th>
      <td>
        <%= text_field_tag 'settings[embedding_model]', 
            settings['embedding_model'] %>
      </td>
    </tr>
    
    <tr>
      <th>LLM Model</th>
      <td>
        <%= text_field_tag 'settings[llm_model]', 
            settings['llm_model'] %>
      </td>
    </tr>
    
    <tr>
      <th>Chunk Size</th>
      <td>
        <%= number_field_tag 'settings[chunk_size]', 
            settings['chunk_size'], 
            min: 100, max: 2000 %>
        <em class="info">Characters per chunk</em>
      </td>
    </tr>
    
    <tr>
      <th>Chunk Overlap</th>
      <td>
        <%= number_field_tag 'settings[chunk_overlap]', 
            settings['chunk_overlap'],
            min: 0, max: 500 %>
        <em class="info">Overlap between chunks</em>
      </td>
    </tr>
    
    <tr>
      <th>Default Features</th>
      <td>
        <label>
          <%= check_box_tag 'settings[use_hyde]', '1', 
              settings['use_hyde'] == '1' %>
          Enable HyDE by default
        </label>
        <br>
        <label>
          <%= check_box_tag 'settings[use_multiquery]', '1', 
              settings['use_multiquery'] == '1' %>
          Enable Multi-Query by default
        </label>
      </td>
    </tr>
  </tbody>
</table>

<div class="contextual">
  <%= link_to 'Test Connection', '#', 
      onclick: "testRagConnection(); return false;",
      class: 'icon icon-test' %>
</div>

<script type="text/javascript">
function testRagConnection() {
  var url = $('#settings_python_service_url').val();
  $.ajax({
    url: url + '/health',
    type: 'GET',
    success: function(data) {
      alert('Connection successful!');
    },
    error: function() {
      alert('Connection failed. Please check the URL.');
    }
  });
}
</script>
```

## Step 12: Stylesheets

### plugins/redmine_rag/assets/stylesheets/rag_search.css

```css
/* RAG Search Styles */
.rag-result {
  border-bottom: 1px solid #e0e0e0;
  padding: 10px 0;
  margin-bottom: 10px;
}

.rag-result h4 {
  margin: 0 0 5px 0;
}

.rag-result .metadata {
  color: #666;
  font-size: 0.9em;
  margin: 5px 0;
}

.rag-result .snippet {
  margin: 10px 0;
  line-height: 1.5;
}

.rag-result .snippet mark {
  background-color: yellow;
  font-weight: bold;
}

.rag-result .ai-summary {
  background-color: #f0f8ff;
  border-left: 3px solid #4CAF50;
  padding: 10px;
  margin-top: 10px;
  font-style: italic;
}

.relevance-score {
  color: #ffa500;
  font-size: 0.9em;
  margin-left: 10px;
}

#rag-search-input {
  width: 100%;
  padding: 8px;
  font-size: 1.1em;
}

.rag-options {
  margin-left: 20px;
}

/* Autocomplete styling */
.ui-autocomplete {
  max-height: 200px;
  overflow-y: auto;
  overflow-x: hidden;
}

.ui-autocomplete li {
  padding: 5px 10px;
}

.ui-autocomplete li:hover {
  background-color: #f0f0f0;
}
```

## Step 13: Rake Tasks

### plugins/redmine_rag/lib/tasks/rag.rake

```ruby
namespace :redmine do
  namespace :rag do
    desc "Index all content for RAG search"
    task :index => :environment do
      puts "Starting RAG indexing..."
      
      # Index all issues
      Issue.find_each do |issue|
        if issue.project.module_enabled?('rag_search')
          RagDocument.index_issue(issue)
          print "."
        end
      end
      
      # Index all wiki pages
      WikiPage.find_each do |page|
        if page.wiki.project.module_enabled?('rag_search')
          RagDocument.index_wiki_page(page)
          print "."
        end
      end
      
      puts "\nIndexing complete!"
    end
    
    desc "Clear RAG index"
    task :clear => :environment do
      puts "Clearing RAG index..."
      RagDocument.destroy_all
      
      # Also clear vector store via API
      service = RedmineRag::RagService.new
      service.clear_index
      
      puts "Index cleared!"
    end
    
    desc "Reindex specific project"
    task :reindex_project, [:project_id] => :environment do |t, args|
      project = Project.find(args[:project_id])
      puts "Reindexing project: #{project.name}"
      
      # Clear existing documents for this project
      RagDocument.where(project_id: project.id).destroy_all
      
      # Reindex issues
      project.issues.find_each do |issue|
        RagDocument.index_issue(issue)
        print "."
      end
      
      # Reindex wiki pages
      if project.wiki
        project.wiki.pages.find_each do |page|
          RagDocument.index_wiki_page(page)
          print "."
        end
      end
      
      puts "\nProject reindexing complete!"
    end
  end
end
```

## Step 14: Localization

### plugins/redmine_rag/config/locales/en.yml

```yaml
en:
  # Permissions
  permission_use_rag_search: Use AI-powered search
  permission_manage_rag_index: Manage RAG index
  
  # Project module
  project_module_rag_search: AI Search
  
  # Labels
  label_rag_search: AI Search
  label_rag_settings: RAG Settings
  label_use_ai_search: Use AI-powered search
  label_relevance_score: Relevance Score
  label_ai_summary: AI Summary
  
  # Messages
  notice_rag_indexing_started: Content indexing has been started
  notice_rag_index_cleared: Search index has been cleared
  error_rag_service_unavailable: AI search service is currently unavailable
  
  # Settings
  setting_rag_python_service_url: Python Service URL
  setting_rag_api_provider: API Provider
  setting_rag_embedding_model: Embedding Model
  setting_rag_llm_model: LLM Model
  setting_rag_chunk_size: Chunk Size
  setting_rag_chunk_overlap: Chunk Overlap
```

## Step 15: Tests

### plugins/redmine_rag/test/functional/rag_search_controller_test.rb

```ruby
require File.expand_path('../../test_helper', __FILE__)

class RagSearchControllerTest < ActionController::TestCase
  fixtures :projects, :users, :issues
  
  def setup
    @project = Project.find(1)
    @project.enable_module!('rag_search')
    @user = User.find(2)
    @request.session[:user_id] = @user.id
    Role.find(1).add_permission! :use_rag_search
  end
  
  def test_index
    get :index, params: { project_id: @project.id }
    assert_response :success
    assert_template 'index'
  end
  
  def test_search_with_query
    get :search, params: { 
      project_id: @project.id,
      q: 'test query'
    }
    assert_response :success
    assert_not_nil assigns(:results)
  end
  
  def test_suggestions
    get :suggestions, params: {
      project_id: @project.id,
      q: 'test'
    }
    assert_response :success
    json = JSON.parse(response.body)
    assert_kind_of Array, json
  end
  
  def test_rag_search_requires_permission
    Role.find(1).remove_permission! :use_rag_search
    get :index, params: { project_id: @project.id }
    assert_response 403
  end
end
```

## Python Service Structure

Create a separate Python service in `redmine_rag_service/`:

### redmine_rag_service/app.py

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn

from rag_pipeline import RAGPipeline

app = FastAPI(title="Redmine RAG Service")
pipeline = RAGPipeline()

class IndexRequest(BaseModel):
    id: str
    content: str
    metadata: Dict

class SearchRequest(BaseModel):
    query: str
    project_id: Optional[int] = None
    user_id: Optional[int] = None
    options: Dict = {}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/index")
async def index_document(request: IndexRequest):
    vector_id = pipeline.index_document(
        request.id,
        request.content,
        request.metadata
    )
    return {"vector_id": vector_id}

@app.post("/search")
async def search(request: SearchRequest):
    results = pipeline.search(
        request.query,
        project_id=request.project_id,
        **request.options
    )
    return results

@app.get("/suggestions")
async def suggestions(q: str):
    return pipeline.get_suggestions(q)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Installation Instructions

1. **Generate the plugin**:
   ```bash
   cd /path/to/redmica
   bundle exec rails generate redmine_plugin RedmineRag
   ```

2. **Copy the implementation files** to the plugin directory

3. **Run migrations**:
   ```bash
   bundle exec rake redmine:plugins:migrate RAILS_ENV=production
   ```

4. **Start the Python service**:
   ```bash
   cd redmine_rag_service
   pip install -r requirements.txt
   python app.py
   ```

5. **Configure the plugin**:
   - Go to Administration > Plugins > Redmine RAG > Configure
   - Set the Python service URL
   - Configure API keys and models

6. **Enable for projects**:
   - Go to Project > Settings > Modules
   - Enable "AI Search" module

7. **Initial indexing**:
   ```bash
   bundle exec rake redmine:rag:index RAILS_ENV=production
   ```

## Testing the Plugin

```bash
# Run plugin tests
RAILS_ENV=test bundle exec rake redmine:plugins:test NAME=redmine_rag

# Test specific controller
RAILS_ENV=test bundle exec rake test \
  TEST=plugins/redmine_rag/test/functional/rag_search_controller_test.rb
```

This implementation follows Redmine's plugin architecture exactly, making it a proper plugin that can be installed, configured, and removed without modifying core Redmine code.