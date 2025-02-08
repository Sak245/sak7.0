# Movie Graph Explorer

This is an interactive movie knowledge graph application built using Streamlit, Neo4j, and the Groq language model. The app allows users to query a movie knowledge graph using natural language, visualize relationships between entities, and explore movie data seamlessly.

## Features

- **Natural Language Query Interface:** Ask questions about movies, directors, genres, and actors.
- **Knowledge Graph Visualization:** View relationships between movies, actors, genres, and directors.
- **Data Management:** Load sample movie datasets from a public CSV source.
- **AI-Powered Query Generation:** Uses the Groq API to convert natural language questions into Cypher queries for Neo4j.

## Technologies Used

- Streamlit
- Neo4j Database
- Groq Language Model
- PyVis for graph visualization
- LangChain Community Graphs

## Installation

1. **Clone the Repository:**
   ```bash
   git clone <repository-link>
   cd movie-graph-explorer
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application:**
   ```bash
   streamlit run app.py
   ```

## Configuration

To configure the application, provide the following credentials in the sidebar:

- **Neo4j URI:** e.g., `neo4j+s://demo.neo4jlabs.com`
- **Neo4j Username:** Default is `movies`
- **Neo4j Password:** Default is `movies`
- **Groq API Key:** Enter your Groq API key to enable AI-driven Cypher query generation.

## Data Loading

Load sample movie data by clicking the "Load Sample Movie Dataset" button. The dataset will be fetched from the following source:

[https://raw.githubusercontent.com/tomasonjo/blog-datasets/main/movies/movies_small.csv](https://raw.githubusercontent.com/tomasonjo/blog-datasets/main/movies/movies_small.csv)

The sample dataset includes movie details, actors, directors, genres, and ratings.

## Usage

1. **Initialize Connections:** Provide the required Neo4j and Groq API credentials and click the "Initialize Connections" button.

2. **Load Data:** Click the "Load Sample Movie Dataset" button to populate the graph database.

3. **Ask Questions:** Enter natural language queries in the input box to get answers and visualize the graph.

### Example Queries

- "Who directed The Matrix?"
- "What genres does Toy Story belong to?"
- "List Tom Hanks' movies"

## Visualization

The graph visualization uses PyVis to display relationships between entities. Nodes represent entities such as movies, actors, directors, and genres, while edges show relationships.

## Styling

The application includes custom styling for a modern and interactive user experience, with intuitive button and input field designs.

## Troubleshooting

1. **Connection Issues:** Ensure that the Neo4j URI, username, and password are correct.
2. **Groq API Key:** Verify that the API key is correctly set and active.
3. **Data Loading Errors:** Ensure that the sample CSV is accessible from the provided link.

## License

This project is licensed under the MIT License. See the LICENSE file for more information.

