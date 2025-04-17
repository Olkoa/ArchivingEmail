import streamlit as st
import duckdb
import pandas as pd

# Initialize DuckDB connection (in-memory)
con = duckdb.connect()

# Create a sample table
con.execute("""
CREATE TABLE products (
    id INTEGER,
    name VARCHAR,
    description VARCHAR
)
""")

# Insert some sample data
con.execute("""
INSERT INTO products VALUES
(1, 'Laptop', 'A powerful laptop with 16GB RAM'),
(2, 'Mouse', 'Wireless ergonomic mouse'),
(3, 'Keyboard', 'Mechanical keyboard with RGB'),
(4, 'Monitor', '27-inch 4K UHD display'),
(5, 'Webcam', '1080p HD webcam with microphone'),
(6, 'Headphones', 'Noise-cancelling over-ear headphones'),
(7, 'Speaker', 'Bluetooth speaker with deep bass'),
(8, 'Printer', 'Wireless color inkjet printer'),
(9, 'Tablet', '10-inch rgb Android tablet with stylus'),
(10, 'Smartphone', 'Latest model with OLED screen'),
(11, 'Router', 'Dual-band WiFi 6 router'),
(12, 'Desk Lamp', 'LED desk lamp with USB charging port'),
(13, 'External Hard Drive', '2TB portable USB 3.0 drive'),
(14, 'USB Hub', '4-port USB 3.0 hub'),
(15, 'Smartwatch', 'Fitness-focused smartwatch with GPS'),
(16, 'Microphone', 'USB condenser mic for podcasts'),
(17, 'Projector', '1080p home cinema projector'),
(18, 'Gaming Chair', 'Ergonomic gaming chair with lumbar support'),
(19, 'Graphics Tablet', 'Digital drawing tablet with pen'),
(20, 'SSD', '1TB NVMe solid state rgb drive')
""")


# Streamlit app layout
st.title("🔍 DuckDB Product Search")

# Search bar
search_query = st.text_input("Enter product keyword", "")

if search_query:
    # Query DuckDB
    df = con.execute(f"""
        SELECT * FROM products
        WHERE LOWER(name) LIKE LOWER('%{search_query}%')
           OR LOWER(description) LIKE LOWER('%{search_query}%')
    """).fetchdf()

    if not df.empty:
        st.success(f"Found {len(df)} result(s):")
        st.dataframe(df)
    else:
        st.warning("No matching products found.")
