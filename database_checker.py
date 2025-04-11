from flask import Flask, render_template, jsonify
import duckdb

# Eventually to make it faster to load we can directly load the react libs & imports we are doing in the head on local to make it faster to execute.
# pip install duckdb flask

app = Flask(__name__)

# Ensure templates directory exists
import os
if not os.path.exists('templates'):
    os.makedirs('templates')

# Create the HTML template
with open('templates/schema.html', 'w') as f:
    f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DuckDB Schema Visualization</title>
    <script src="https://unpkg.com/react@17/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@17/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/babel-standalone@6/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <div id="root"></div>

    <script type="text/babel">
        const SchemaVisualizer = () => {
            const [tables, setTables] = React.useState([]);
            const [searchTerm, setSearchTerm] = React.useState('');
            const [expandedTables, setExpandedTables] = React.useState({});
            const [loading, setLoading] = React.useState(true);

            React.useEffect(() => {
                // Fetch schema data from the API endpoint
                fetch('/api/schema')
                    .then(response => response.json())
                    .then(data => {
                        setTables(data);
                        setLoading(false);

                        // Auto-expand tables if there are only a few
                        if (data.length <= 5) {
                            const expanded = {};
                            data.forEach(table => {
                                expanded[table.name] = true;
                            });
                            setExpandedTables(expanded);
                        }
                    })
                    .catch(error => {
                        console.error("Error fetching schema data:", error);
                        setLoading(false);
                    });
            }, []);

            // Filter tables based on search term
            const filteredTables = tables.filter(table =>
                table.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                table.columns.some(col =>
                    col.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    col.type.toLowerCase().includes(searchTerm.toLowerCase())
                )
            );

            // Toggle expanded state for a table
            const toggleTableExpanded = (tableName) => {
                setExpandedTables(prev => ({
                    ...prev,
                    [tableName]: !prev[tableName]
                }));
            };

            if (loading) {
                return (
                    <div className="flex items-center justify-center h-screen">
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700 mx-auto"></div>
                            <p className="mt-3 text-gray-600">Loading database schema...</p>
                        </div>
                    </div>
                );
            }

            return (
                <div className="container mx-auto p-4">
                    <h1 className="text-3xl font-bold mb-6 text-center text-blue-800">DuckDB Schema Visualization</h1>

                    {/* Search bar */}
                    <div className="mb-6">
                        <input
                            type="text"
                            placeholder="Search tables or columns..."
                            className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>

                    {/* Table statistics */}
                    <div className="mb-6 text-center text-gray-600">
                        <p>Database contains {tables.length} tables with a total of {tables.reduce((acc, table) => acc + table.columns.length, 0)} columns</p>
                    </div>

                    {/* Tables */}
                    <div className="space-y-4">
                        {filteredTables.map((table) => (
                            <div
                                key={table.name}
                                className="border border-gray-300 rounded-lg bg-white shadow-sm overflow-hidden transition duration-200 hover:shadow-md"
                            >
                                {/* Table header */}
                                <div
                                    className="bg-blue-600 text-white p-3 flex justify-between items-center cursor-pointer hover:bg-blue-700"
                                    onClick={() => toggleTableExpanded(table.name)}
                                >
                                    <h2 className="font-bold text-lg">{table.name}</h2>
                                    <div className="flex items-center space-x-2">
                                        <span className="text-xs bg-blue-800 px-2 py-1 rounded-full">
                                            {table.columns.length} columns
                                        </span>
                                        <span>{expandedTables[table.name] ? '▼' : '►'}</span>
                                    </div>
                                </div>

                                {/* Table content */}
                                {expandedTables[table.name] && (
                                    <div className="p-0">
                                        <table className="w-full">
                                            <thead className="bg-gray-100">
                                                <tr>
                                                    <th className="py-2 px-4 text-left font-medium text-gray-600">Column</th>
                                                    <th className="py-2 px-4 text-left font-medium text-gray-600">Type</th>
                                                    <th className="py-2 px-4 text-left font-medium text-gray-600">Key</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {table.columns.map((column, idx) => (
                                                    <tr
                                                        key={column.name}
                                                        className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                                                    >
                                                        <td className="py-2 px-4 border-t border-gray-200">
                                                            {column.name}
                                                        </td>
                                                        <td className="py-2 px-4 border-t border-gray-200 text-gray-600">
                                                            {column.type}
                                                        </td>
                                                        <td className="py-2 px-4 border-t border-gray-200">
                                                            {column.isPrimary && <span className="text-yellow-600 font-bold" title="Primary Key">PK</span>}
                                                            {column.isForeign && (
                                                                <span className="text-blue-600 ml-1" title={`Foreign Key to ${column.references}`}>
                                                                    FK → {column.references}
                                                                </span>
                                                            )}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>

                    {filteredTables.length === 0 && (
                        <div className="text-center text-gray-500 my-10 p-10 border border-gray-200 rounded-lg">
                            No tables found matching your search criteria
                        </div>
                    )}
                </div>
            );
        };

        // Render the application
        ReactDOM.render(<SchemaVisualizer />, document.getElementById('root'));
    </script>
</body>
</html>
    ''')

@app.route('/')
def index():
    """Render the schema visualization page"""
    return render_template('schema.html')

@app.route('/api/schema')
def get_schema():
    """API endpoint to get the database schema as JSON"""
    # Connect to your DuckDB database
    conn = duckdb.connect('data/database/database.duckdb')  # Change to your database path

    # Get all tables and columns
    schema_data = conn.execute("""
        SELECT
            table_schema,
            table_name,
            column_name,
            data_type
        FROM information_schema.columns
        WHERE table_schema = 'main'
        ORDER BY table_name, ordinal_position
    """).fetchall()

    print(schema_data)

    # Structure the data for the frontend
    tables_map = {}

    for schema, table_name, column_name, data_type in schema_data:
        if table_name not in tables_map:
            tables_map[table_name] = {
                "name": table_name,
                "schema": schema,
                "columns": []
            }

        # Determine primary/foreign keys based on naming conventions
        is_primary = column_name == 'id'
        is_foreign = column_name.endswith('_id') and column_name != 'id'
        references = column_name.replace('_id', '') if is_foreign else None

        tables_map[table_name]["columns"].append({
            "name": column_name,
            "type": data_type,
            "isPrimary": is_primary,
            "isForeign": is_foreign,
            "references": references
        })

    return jsonify(list(tables_map.values()))

if __name__ == '__main__':
    app.run(debug=True)
