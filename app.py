import streamlit as st
from seo_tool import LLMIntegration, SERPScraper, ContentScorer, KeywordAnalyzer, SEOAnalyzer
import json

# Set page configuration
st.set_page_config(
    page_title="SEO Content Optimizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize core components
llm_integration = LLMIntegration()
serp_scraper = SERPScraper()
keyword_analyzer = KeywordAnalyzer(llm_integration)
content_scorer = ContentScorer()
seo_analyzer = SEOAnalyzer(llm_integration, serp_scraper, keyword_analyzer, content_scorer)

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
    .priority-high {
        border-left-color: #dc3545;
    }
    .priority-medium {
        border-left-color: #ffc107;
    }
    .priority-low {
        border-left-color: #0dcaf0;
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
    if openai_api_key:
        llm_integration.api_key = openai_api_key
    
    st.info("Enter your OpenAI API key to enable AI-powered recommendations")

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
                competitors = seo_analyzer.analyze_serp_competitors(keyword)
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
                    recommendations = seo_analyzer.generate_content_recommendations(
                        content, st.session_state.current_keyword, st.session_state.competitors
                    )
                    
                    score = seo_analyzer.calculate_optimization_score(
                        content, st.session_state.current_keyword, st.session_state.competitors
                    )
                
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
                research = seo_analyzer.generate_keyword_research(research_keyword)
            
            try:
                # Try to parse as JSON
                research_data = json.loads(research)
                
                st.subheader("Related Keywords")
                related_df = pd.DataFrame(research_data['related_keywords'])
                st.dataframe(related_df)
                
                st.subheader("LSI Keywords")
                st.write(", ".join(research_data['lsi_keywords']))
                
                st.subheader("Keyword Clusters")
                for cluster in research_data['clusters']:
                    st.write(f"**{cluster['theme']}**: {', '.join(cluster['keywords'])}")
                
                st.subheader("Content Gaps")
                for gap in research_data['content_gaps']:
                    st.write(f"- {gap}")
                    
            except json.JSONDecodeError:
                # If not JSON, display as plain text
                st.info("Keyword Research Results:")
                st.write(research)

with tab4:
    st.header("Content Brief Generator")
    
    if not st.session_state.current_keyword:
        st.warning("Please analyze a keyword first in the 'Keyword Analysis' tab")
    else:
        st.info(f"Generating brief for keyword: {st.session_state.current_keyword}")
        
        if st.button("Generate Content Brief", key="brief_btn"):
            with st.spinner("Creating content brief..."):
                brief = seo_analyzer.create_content_brief(
                    st.session_state.current_keyword, st.session_state.competitors
                )
            
            st.subheader("Content Brief")
            st.write(brief)

def get_score_class(score):
    if score >= 80:
        return "score-excellent"
    elif score >= 60:
        return "score-good"
    elif score >= 40:
        return "score-fair"
    else:
        return "score-poor"

# Footer
st.markdown("---")
st.markdown("### 📝 How to Use This Tool")
st.markdown("""
1. **Keyword Analysis**: Enter a keyword to analyze top competitors in search results
2. **Content Optimization**: Paste your content to get optimization recommendations
3. **Keyword Research**: Generate related keywords and content ideas
4. **Content Brief**: Create a detailed content brief for your target keyword
""")
