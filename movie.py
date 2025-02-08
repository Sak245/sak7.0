import streamlit as st
import os
import time
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_groq import ChatGroq
from pyvis.network import Network
from streamlit.components.v1 import html
from neo4j.graph import Node, Relationship

# Initialize placeholders at the start
connection_status = st.empty()
data_loading_status = st.empty()
query_result_placeholder = st.empty()
graph_placeholder = st.empty()

# Streamlit Configuration
st.set_page_config(page_title="Movie Graph Explorer", layout="wide")
st.title("🎬 Intelligent Movie Knowledge Graph")
st.subheader("Natural Language Query Interface with Visual Exploration")

# Sidebar Configuration
with st.sidebar:
    st.header("🔐 Connection Settings")
    neo4j_uri = st.text_input("Neo4j URI", value="neo4j+s://demo.neo4jlabs.com")
    neo4j_user = st.text_input("Username", value="movies")
    neo4j_pass = st.text_input("Password", type="password", value="movies")
    groq_key = st.text_input("GROQ API Key", type="password")
    
    if st.button("Initialize Connections"):
        with connection_status:
            st.info("Connecting to databases...")
            try:
                graph = Neo4jGraph(url=neo4j_uri, username=neo4j_user, password=neo4j_pass)
                os.environ["GROQ_API_KEY"] = groq_key
                llm = ChatGroq(temperature=0, model_name="mixtral-8x7b-32768")
                connection_status.success("Connected successfully!")
            except Exception as e:
                connection_status.error(f"Connection failed: {str(e)}")

# Data Loading Section
if 'graph' in locals() and 'llm' in locals():
    with st.sidebar:
        st.header("📥 Data Management")
        if st.button("Load Sample Movie Dataset"):
            with data_loading_status:
                st.info("Loading movie data...")
                try:
                    load_query = """
                    LOAD CSV WITH HEADERS FROM 
                    'https://raw.githubusercontent.com/tomasonjo/blog-datasets/main/movies/movies_small.csv' 
                    AS row
                    MERGE (m:Movie {id: row.movieId})
                    SET m.released = date(row.released),
                        m.title = row.title,
                        m.imdbRating = toFloat(row.imdbRating)
                    FOREACH (director IN split(row.director, '|') | 
                        MERGE (d:Person {name: trim(director)})
                        MERGE (d)-[:DIRECTED]->(m))
                    FOREACH (actor IN split(row.actors, '|') | 
                        MERGE (a:Person {name: trim(actor)})
                        MERGE (a)-[:ACTED_IN]->(m))
                    FOREACH (genre IN split(row.genres, '|') | 
                        MERGE (g:Genre {name: trim(genre)})
                        MERGE (m)-[:IN_GENRE]->(g))
                    """
                    graph.query(load_query)
                    data_loading_status.success("Loaded 32 movies with relationships!")
                except Exception as e:
                    data_loading_status.error(f"Data loading error: {str(e)}")

# Query Interface
if 'graph' in locals() and 'llm' in locals():
    query = st.text_input("Enter your question about movies, actors, or genres:")
    
    if query:
        with query_result_placeholder.container():
            st.info("Processing your query...")
            progress_bar = st.progress(0)
            
            try:
                # Initial processing
                progress_bar.progress(25)
                time.sleep(0.5)
                
                # Cypher Generation Setup
                examples = [
                    {
                        "question": "Who directed The Matrix?",
                        "query": "MATCH (m:Movie {title: 'The Matrix'})<-[:DIRECTED]-(d) RETURN d.name"
                    },
                    {
                        "question": "What genres does Toy Story belong to?",
                        "query": "MATCH (m:Movie {title: 'Toy Story'})-[:IN_GENRE]->(g) RETURN collect(g.name)"
                    }
                ]
                
                prompt = FewShotPromptTemplate(
                    examples=examples,
                    example_prompt=PromptTemplate.from_template(
                        "Question: {question}\nCypher: {query}"
                    ),
                    prefix="Generate precise Cypher queries for movie questions:",
                    suffix="Question: {input}\nCypher:",
                    input_variables=["input"]
                )

                # Execute Query
                progress_bar.progress(50)
                chain = GraphCypherQAChain.from_llm(
                    llm=llm,
                    graph=graph,
                    cypher_prompt=prompt,
                    return_intermediate_steps=True,
                    verbose=True
                )
                result = chain.invoke(query)
                
                # Process Results
                progress_bar.progress(75)
                answer = result["result"]
                cypher_query = result["intermediate_steps"]["query"]
                graph_data = graph.query(cypher_query.replace("RETURN", "WITH * LIMIT 50 RETURN"))
                
                # Visualization Logic
                net = Network(height="600px", width="100%", notebook=True)
                has_graph_elements = False
                
                for record in graph_data:
                    for item in record:
                        if isinstance(item, Node):
                            has_graph_elements = True
                            node_id = item.id
                            label = item.get("title") or item.get("name") or list(item.labels)[0]
                            net.add_node(node_id, label=label, group=list(item.labels)[0])
                            
                        elif isinstance(item, Relationship):
                            has_graph_elements = True
                            net.add_edge(
                                item.start_node.id, 
                                item.end_node.id, 
                                title=item.type
                            )

                # Update placeholders
                query_result_placeholder.empty()
                with query_result_placeholder.container():
                    st.subheader("Text Response")
                    st.write(answer)
                    st.markdown(f"**Generated Cypher:**\n``````")

                    if has_graph_elements:
                        graph_placeholder.empty()
                        with graph_placeholder.container():
                            st.subheader("Knowledge Graph")
                            net.save_graph("graph.html")
                            html(open("graph.html", encoding="utf-8").read(), height=600)
                    else:
                        graph_placeholder.info("🔍 No graph elements found in query results")

                progress_bar.progress(100)
                time.sleep(0.5)
                progress_bar.empty()

            except Exception as e:
                query_result_placeholder.error(f"Query failed: {str(e)}")
                graph_placeholder.empty()

# Styling
st.markdown("""
<style>
    [data-testid=stSidebar] {
        background: #f8f9fa!important;
        border-right: 1px solid #eee;
    }
    .stButton>button {
        transition: all 0.2s;
    }
    .stTextInput>div>div>input {
        border-radius: 8px!important;
    }
</style>
""", unsafe_allow_html=True)
