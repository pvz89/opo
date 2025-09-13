import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import json
import openai
import pandas as pd
import numpy as np
from collections import Counter
import time
import random

# Initialize session state
if 'current_keyword' not in st.session_state:
    st.session_state.current_keyword = ''
if 'competitors' not in st.session_state:
    st.session_state.competitors = []

# Set page configuration
st.set_page_config(
    page_title="SEO Content Optimizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .score-card {
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .score-excellent {
        background-color: #d4edda;
        color: #155724;
    }
    .score-good {
        background-color: #d1ecf1;
        color: #0c5460;
    }
    .score-fair {
        background-color: #fff3cd;
        color: #856404;
    }
    .score-poor {
        background-color: #f8d7da;
        color: #721c24;
    }
    .recommendation {
        padding: 15px;
        margin-bottom: 10px;
        border-left: 4px solid #0d6efd;
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# App title
st.title("📊 SEO Content Optimization Tool")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    openai_api_key = st.text_input("OpenAI API Key", type="password", 
                                  value=st.secrets.get("OPENAI_API_KEY", "") if st.secrets.get("OPENAI_API_KEY") else "")
    
    st.info("Enter your OpenAI API key to enable AI-powered recommendations")

# Simple LLM Integration
def generate_ai_response(prompt, max_tokens=1000):
    try:
        if not openai_api_key:
            return "Error: OpenAI API key not configured. Please add it in the sidebar."
            
        openai.api_key = openai_api_key
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an SEO expert with 10+ years of experience. Provide detailed, actionable recommendations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        return response.choices[0].message['content']
    except Exception as e:
        return f"Error generating response: {str(e)}"

# SERP Scraper
def scrape_top_results(keyword, num_results=10):
    # Mock data for demonstration
    mock_results = [
        {'position': 1, 'title': f'Example Page 1 for {keyword}', 'url': f'https://example.com/{keyword.replace(" ", "-")}'},
        {'position': 2, 'title': f'Example Page 2 for {keyword}', 'url': f'https://example.org/{keyword.replace(" ", "-")}'},
        {'position': 3, 'title': f'Example Page 3 for {keyword}', 'url': f'https://example.net/{keyword.replace(" ", "-")}'}
    ]
    
    return mock_results[:num_results]

def extract_page_data(url):
    try:
        # Add delay to be respectful to servers
        time.sleep(random.uniform(1, 3))
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.find('title').get_text() if soup.find('title') else ''
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc.get('content') if meta_desc else ''
        
        # Extract text content (simplified)
        text = ' '.join([p.get_text() for p in soup.find_all('p')])
        
        return {
            'url': url,
            'title': title,
            'meta_description': meta_description,
            'text': text
        }
        
    except Exception as e:
        return {
            'url': url,
            'error': str(e)
        }

# Content Scoring
def calculate_readability(text):
    # Simplified Flesch Reading Ease calculation
    sentences = text.split('.')
    words = text.split()
    
    if len(sentences) == 0 or len(words) == 0:
        return 0
        
    avg_sentence_length = len(words) / len(sentences)
    
    # Simple syllable count approximation
    vowels = 'aeiouy'
    total_syllables = 0
    for word in words:
        prev_char_vowel = False
        syllables = 0
        
        for char in word.lower():
            if char in vowels and not prev_char_vowel:
                syllables += 1
            prev_char_vowel = char in vowels
        
        if syllables == 0:
            syllables = 1
            
        total_syllables += syllables
    
    avg_syllables_per_word = total_syllables / len(words)
    
    readability = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
    return max(0, min(100, readability))

def analyze_serp_competitors(keyword, num_results=10):
    # Scrape top search results
    results = scrape_top_results(keyword, num_results)
    
    competitors = []
    for result in results:
        # Extract page data
        page_data = extract_page_data(result['url'])
        
        # Analyze page metrics
        text_content = page_data.get('text', '')
        
        # Calculate keyword density
        words = re.findall(r'\w+', text_content.lower())
        word_count = len(words)
        keyword_occurrences = words.count(keyword.lower())
        keyword_density = (keyword_occurrences / word_count) * 100 if word_count > 0 else 0
        
        competitors.append({
            'url': result['url'],
            'title': result['title'],
            'position': result.get('position', 0),
            'word_count': word_count,
            'keyword_density': round(keyword_density, 2),
            'readability_score': calculate_readability(text_content)
        })
    
    return competitors

def score_content(content, keyword, competitors):
    # Calculate keyword density
    words = re.findall(r'\w+', content.lower())
    word_count = len(words)
    keyword_occurrences = words.count(keyword.lower())
    keyword_density = (keyword_occurrences / word_count) * 100 if word_count > 0 else 0
    
    # Calculate scores
    keyword_score = max(0, min(100, 100 - abs(keyword_density - 1.5) * 20))
    quality_score = calculate_readability(content)
    technical_score = 50  # Placeholder
    competitive_score = 50  # Placeholder
    
    # Weighted average
    total_score = (
        keyword_score * 0.3 +
        quality_score * 0.25 +
        technical_score * 0.25 +
        competitive_score * 0.2
    )
    
    # Check for over-optimization
    warnings = []
    if keyword_density > 2.5:
        warnings.append(f"High keyword density ({round(keyword_density, 1)}%) - may be considered keyword stuffing")
    
    return {
        'total_score': round(total_score, 1),
        'category_scores': {
            'keyword_optimization': round(keyword_score, 1),
            'content_quality': round(quality_score, 1),
            'technical_seo': round(technical_score, 1),
            'competitive_alignment': round(competitive_score, 1)
        },
        'warnings': warnings
    }

def get_score_class(score):
    if score >= 80:
        return "score-excellent"
    elif score >= 60:
        return "score-good"
    elif score >= 40:
        return "score-fair"
    else:
        return "score-poor"

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["Keyword Analysis", "Content Optimization", "Keyword Research", "Content Brief"])

with tab1:
    st.header("Keyword Analysis")
    
    keyword = st.text_input("Enter target keyword", key="keyword_input")
    
    if st.button("Analyze Competitors", key="analyze_btn"):
        if not keyword:
            st.error("Please enter a keyword")
        else:
            with st.spinner("Analyzing competitors..."):
                competitors = analyze_serp_competitors(keyword)
                st.session_state.current_keyword = keyword
                st.session_state.competitors = competitors
            
            st.success(f"Analysis complete for '{keyword}'")
            
            # Display competitor data
            st.subheader("Top Competitors")
            competitor_df = pd.DataFrame(competitors)
            st.dataframe(competitor_df[['position', 'title', 'url', 'word_count', 'keyword_density', 'readability_score']])

with tab2:
    st.header("Content Optimization")
    
    if not st.session_state.current_keyword:
        st.warning("Please analyze a keyword first in the 'Keyword Analysis' tab")
    else:
        st.info(f"Optimizing for keyword: {st.session_state.current_keyword}")
        
        content = st.text_area("Paste your content here", height=300)
        
        if st.button("Optimize Content", key="optimize_btn"):
            if not content:
                st.error("Please enter some content")
            else:
                with st.spinner("Analyzing content..."):
                    # Generate recommendations
                    prompt = f"""
                    Analyze this content for the keyword "{st.session_state.current_keyword}":
                    
                    Content to analyze:
                    {content}
                    
                    Provide specific recommendations for:
                    1. Keyword optimization
                    2. Content structure improvements
                    3. Technical SEO enhancements
                    4. User experience improvements
                    
                    Rank suggestions by priority (High, Medium, Low) and provide implementation guidance.
                    """
                    
                    recommendations = generate_ai_response(prompt, 1000)
                    
                    # Calculate score
                    score = score_content(content, st.session_state.current_keyword, st.session_state.competitors)
                
                # Display scores
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    score_class = get_score_class(score['total_score'])
                    st.markdown(f"""
                    <div class="score-card {score_class}">
                        <h5>Overall Score</h5>
                        <h2 class="text-center">{score['total_score']}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    score_class = get_score_class(score['category_scores']['keyword_optimization'])
                    st.markdown(f"""
                    <div class="score-card {score_class}">
                        <h6>Keyword Optimization</h6>
                        <h4 class="text-center">{score['category_scores']['keyword_optimization']}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    score_class = get_score_class(score['category_scores']['content_quality'])
                    st.markdown(f"""
                    <div class="score-card {score_class}">
                        <h6>Content Quality</h6>
                        <h4 class="text-center">{score['category_scores']['content_quality']}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    score_class = get_score_class(score['category_scores']['technical_seo'])
                    st.markdown(f"""
                    <div class="score-card {score_class}">
                        <h6>Technical SEO</h6>
                        <h4 class="text-center">{score['category_scores']['technical_seo']}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col5:
                    score_class = get_score_class(score['category_scores']['competitive_alignment'])
                    st.markdown(f"""
                    <div class="score-card {score_class}">
                        <h6>Competitive Alignment</h6>
                        <h4 class="text-center">{score['category_scores']['competitive_alignment']}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Display warnings
                if score['warnings']:
                    st.warning("Optimization Warnings:")
                    for warning in score['warnings']:
                        st.write(f"- {warning}")
                
                # Display recommendations
                st.subheader("Optimization Recommendations")
                st.markdown(f'<div class="recommendation">{recommendations}</div>', unsafe_allow_html=True)

with tab3:
    st.header("Keyword Research")
    
    research_keyword = st.text_input("Enter seed keyword", key="research_keyword")
    
    if st.button("Generate Research", key="research_btn"):
        if not research_keyword:
            st.error("Please enter a keyword")
        else:
            with st.spinner("Generating keyword research..."):
                prompt = f"""
                Generate comprehensive keyword research for the seed keyword "{research_keyword}".
                
                Include:
                1. 20-30 related keywords with search intent classification (informational, commercial, navigational, transactional)
                2. 15-20 LSI keywords
                3. Keyword difficulty estimates (0-100 scale)
                4. Semantic clustering of keywords
                5. Content gap opportunities
                
                Format the response as a JSON object with the following structure:
                {{
                    "primary_keyword": "{research_keyword}",
                    "related_keywords": [
                        {{
                            "keyword": "example",
                            "intent": "informational",
                            "difficulty": 45,
                            "volume": 1000
                        }}
                    ],
                    "lsi_keywords": ["example1", "example2"],
                    "clusters": [
                        {{
                            "theme": "example theme",
                            "keywords": ["keyword1", "keyword2"]
                        }}
                    ],
                    "content_gaps": ["topic1", "topic2"]
                }}
                """
                
                research = generate_ai_response(prompt, 1500)
            
            st.subheader("Keyword Research Results")
            st.write(research)

with tab4:
    st.header("Content Brief Generator")
    
    if not st.session_state.current_keyword:
        st.warning("Please analyze a keyword first in the 'Keyword Analysis' tab")
    else:
        st.info(f"Generating brief for keyword: {st.session_state.current_keyword}")
        
        if st.button("Generate Content Brief", key="brief_btn"):
            with st.spinner("Creating content brief..."):
                prompt = f"""
                Create a detailed content brief for ranking #1 for the keyword "{st.session_state.current_keyword}".
                
                Include:
                1. Recommended word count
                2. Optimal content structure with headings
                3. Keyword integration plan
                4. Technical specifications
                5. Unique angles to outperform competitors
                6. Success metrics to track
                """
                
                brief = generate_ai_response(prompt, 1200)
            
            st.subheader("Content Brief")
            st.write(brief)

# Footer
st.markdown("---")
st.markdown("### 📝 How to Use This Tool")
st.markdown("""
1. **Keyword Analysis**: Enter a keyword to analyze top competitors in search results
2. **Content Optimization**: Paste your content to get optimization recommendations
3. **Keyword Research**: Generate related keywords and content ideas
4. **Content Brief**: Create a detailed content brief for your target keyword
""")
