import streamlit as st
import os
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_groq import ChatGroq
from pyvis.network import Network
from streamlit.components.v1 import html
from neo4j.graph import Node, Relationship

# Streamlit Configuration
st.set_page_config(page_title="Movie Graph Explorer", layout="wide")
st.title("🎬 Intelligent Movie Knowledge Graph")
st.subheader("Natural Language Query Interface with Visual Exploration")

# Initialize Connections
graph = None
llm = None

# Sidebar Configuration
with st.sidebar:
    st.header("🔐 Connection Settings")
    neo4j_uri = st.text_input("Neo4j URI", value="neo4j+s://demo.neo4jlabs.com")
    neo4j_user = st.text_input("Username", value="movies")
    neo4j_pass = st.text_input("Password", type="password", value="movies")
    groq_key = st.text_input("GROQ API Key", type="password")
    
    if st.button("Initialize Connections"):
        try:
            graph = Neo4jGraph(url=neo4j_uri, username=neo4j_user, password=neo4j_pass)
            os.environ["GROQ_API_KEY"] = groq_key
            llm = ChatGroq(temperature=0, model_name="mixtral-8x7b-32768")
            st.success("Connected successfully!")
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")

# Data Loading Section
if graph and llm:
    with st.sidebar:
        st.header("📥 Data Management")
        if st.button("Load Sample Movie Dataset"):
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
                st.success("Loaded 32 movies with relationships!")
            except Exception as e:
                st.error(f"Data loading error: {str(e)}")

# Query Interface
if graph and llm:
    st.header("🔍 Ask About Movies")
    query = st.text_input("Enter your question about movies, actors, or genres:")
    
    if query:
        try:
            # Cypher Generation Setup
            examples = [
                {
                    "question": "Who directed The Matrix?",
                    "query": "MATCH (m:Movie {title: 'The Matrix'})<-[:DIRECTED]-(d) RETURN d.name"
                },
                {
                    "question": "What genres does Toy Story belong to?",
                    "query": "MATCH (m:Movie {title: 'Toy Story'})-[:IN_GENRE]->(g) RETURN collect(g.name)"
                },
                {
                    "question": "List Tom Hanks' movies",
                    "query": "MATCH (a:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m) RETURN collect(m.title)"
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
            chain = GraphCypherQAChain.from_llm(
                llm=llm,
                graph=graph,
                cypher_prompt=prompt,
                return_intermediate_steps=True,
                verbose=True
            )
            result = chain.invoke(query)
            
            # Process Results
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

            # Display Results
            if has_graph_elements:
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.subheader("Text Response")
                    st.write(answer)
                    st.markdown(f"**Generated Cypher:**\n``````")
                
                with col2:
                    st.subheader("Knowledge Graph")
                    net.save_graph("graph.html")
                    html(open("graph.html", encoding="utf-8").read(), height=600)
            else:
                st.subheader("Query Results")
                st.write(answer)
                st.markdown(f"**Generated Cypher:**\n``````")
                st.info("🔍 No graph elements found in query results")

        except Exception as e:
            st.error(f"Query failed: {str(e)}")

# Styling
st.markdown("""
<style>
    [data-testid=stSidebar] {
        background: #f8f9fa!important;
        border-right: 1px solid #eee;
    }
    .stButton>button {
        background: #4CAF50!important;
        color: white!important;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        opacity: 0.9;
        transform: scale(1.02);
    }
    .stTextInput>div>div>input {
        border: 2px solid #4CAF50!important;
        border-radius: 8px!important;
    }
</style>
""", unsafe_allow_html=True)
