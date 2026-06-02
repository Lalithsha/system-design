# System Design: Database Sharding & Application-Level Routing

## 1. Summary
This document outlines the implementation of **Database Sharding** (Horizontal Partitioning) using PostgreSQL, Docker, and a Node.js API layer. While Read Replicas scale "Read" operations, Sharding scales "Write" and "Storage" operations by splitting data across multiple independent database nodes based on a defined routing algorithm.

---

## 2. Architecture & Approach

### The System Design Concept
* **Shards:** Independent database instances that hold a specific subset of the total data.
* **Shard Key:** A specific attribute of the data (in this case, `userId`) used to determine which shard the data belongs to.
* **Application-Level Routing:** The database itself is unaware of the sharding. The application (API) holds the connection details for all shards and contains the logic to route the request to the correct physical database.
* **Modulo Hashing:** The specific algorithmic approach used to distribute data. Formula: `target_shard = User_ID % Total_Shards`.

### The Implementation Strategy
* **Infrastructure:** Two independent PostgreSQL containers (`shard-0` and `shard-1`) running on a shared Docker network, exposed to the host machine on different ports (`5432` and `5433`).
* **API Layer:** An Express.js Node server maintaining distinct connection pools to both databases.
* **Routing Interceptor:** A middleware/function (`getTargetShard`) that intercepts incoming read/write requests, calculates the modulo hash of the provided ID, and returns the correct database connection pool before executing the SQL query.

---

## 3. Visual Architecture & Data Flow

```text
                             [ 📱 Client Application ]
                                        |
                                        | HTTP POST (Write) / GET (Read)
                                        | Payload: { "id": 42 }
                                        v
                         +-----------------------------+
                         |       Node.js API           |
                         |      (Port: 3000)           |
                         |                             |
                         |  Router: id % 2 = target    |
                         +-----------------------------+
                                        |
                 +----------------------+----------------------+
                 | (If Target = 0)                             | (If Target = 1)
                 v                                             v
     +-----------------------+                     +-----------------------+
     |       SHARD 0         |                     |       SHARD 1         |
     |     (Even IDs)        |                     |      (Odd IDs)        |
     |-----------------------|                     |-----------------------|
     |                       |                     |                       |
     |  [ 👑 Primary 0 ] <-------(Writes)          |  [ 👑 Primary 1 ] <-------(Writes)
     |  (Port: 5432)         |                     |  (Port: 5433)         |
     |          |            |                     |          |            |
     |          |            |                     |          |            |
     |          | (WAL Stream)                     |          | (WAL Stream)
     |          v            |                     |          v            |
     |          |            |                     |          |            |
     |  [ 👓 Replica 0 ] <-------(Reads)           |  [ 👓 Replica 1 ] <-------(Reads)
     |  (Read-Only)          |                     |  (Read-Only)          |
     +-----------------------+                     +-----------------------+
```

### How Data Flows Through This Architecture:
1. **The Request:** The Client asks to read or write a user with `id: 42`.
2. **The API Routing (Sharding):** The Node.js application calculates `42 % 2 = 0`. It instantly knows this request must be routed down the **left path** to Shard 0.
3. **Write vs. Read Routing (Replication):** * If it is a `POST` request (Write), the API connects directly to **Primary 0** to insert the data.
   * If it is a `GET` request (Read), the API connects directly to **Replica 0** to fetch the data without bothering the Primary.
4. **The Silent Sync (WAL):** Behind the scenes, the Primary databases are continuously streaming their Write-Ahead Logs (WAL) down to their respective Replicas, ensuring the Replicas always have the latest data ready for the next Read request.

---

## 4. Configuration & Code

### A. Infrastructure (docker-compose.yml)
```yaml
services: 
  shard-0:
    image: postgres:15
    container_name: shard-0
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: userdb
    ports:
      - 5432:5432

  shard-1:
    image: postgres:15
    container_name: shard-1
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: userdb
    ports:
      - 5433:5432
```

### B. Node Environment (package.json)
Note the inclusion of `"type": "module"` to allow modern ES6 import syntax instead of CommonJS require syntax.
```json
{
  "name": "sharding-with-horizontal-scaling",
  "version": "1.0.0",
  "main": "server.js",
  "type": "module",
  "dependencies": {
    "express": "^4.19.2",
    "pg": "^8.11.5"
  }
}
```

### C. Application Routing Logic (server.js)
```javascript
import express from 'express';
import { Pool } from 'pg';

const app = express();
app.use(express.json());

// 1. Connection Pools (Using 127.0.0.1 to force IPv4 and bypass host OS DBs)
const shard0 = new Pool({
    host: '127.0.0.1',
    port: 5432,
    user: 'postgres',
    password: 'password',
    database: 'userdb'
});

const shard1 = new Pool({
    host: '127.0.0.1',
    port: 5433, 
    user: 'postgres', 
    password: 'password',
    database: 'userdb'
});

// 2. The Routing Algorithm (Modulo Hashing)
function getTargetShard(userId) {
    const shardId = userId % 2;
    console.log(`Routing user ${userId} to Shard ${shardId}`);
    return shardId === 0 ? shard0 : shard1; 
} 

// 3. WRITE API (Routed dynamically)
app.post('/users', async (req, res) => {
    const { id, name } = req.body;
    const targetDatabase = getTargetShard(id);
   
    try {
        await targetDatabase.query('CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY, name VARCHAR(100));');
        await targetDatabase.query('INSERT INTO users (id, name) VALUES ($1, $2)', [id, name]);
        res.send(`Successfully saved ${name} to Shard ${id % 2}\n`);
    } catch (err) {
        console.error('Error saving user:', err);
        res.status(500).send(err.message);    
    }
}); 

// 4. READ API (Routed dynamically)
app.get('/users/:id', async (req, res) => {
    const userId = parseInt(req.params.id);
    const targetDatabase = getTargetShard(userId);

    try {
        const result = await targetDatabase.query('SELECT * FROM users WHERE id = $1', [userId]);
        if (result.rows.length > 0) {
            res.json(result.rows[0]);
        } else {
            res.status(404).send("User not found");
        }
    } catch (err) {
        console.error('Error reading user:', err);
        res.status(500).send(err.message);
    }
});

app.listen(3000, () => {
    console.log('Server is running on port 3000');
});
```

---

## 5. Key Learnings & Pitfalls

### IPv4 vs IPv6 Localhost Resolution
* **Issue:** Connecting to `localhost:5432` resulted in a `role "postgres" does not exist` error.
* **Root Cause:** Modern Node.js versions resolve `localhost` to the IPv6 address `::1` before the IPv4 address `127.0.0.1`. If the host machine (e.g., a Mac) has a native PostgreSQL instance running on `::1`, Node connects to the native host DB instead of the Docker container.
* **Resolution:** Hardcode the connection string to `127.0.0.1` to explicitly force an IPv4 connection, ensuring traffic is routed to Docker's exposed port.

### ES Modules vs CommonJS
* **Issue:** `SyntaxError: Cannot use import statement outside a module`
* **Root Cause:** Node.js defaults to CommonJS module resolution (`require()`). Using modern ES6 `import` syntax will crash the application if Node isn't configured to expect it.
* **Resolution:** Add `"type": "module"` to the top level of the `package.json` file.

### Container Naming Conflicts
* **Issue:** `Error response from daemon: Conflict. The container name "/shard-1" is already in use...`
* **Root Cause:** Docker container names must be globally unique across the system. 
* **Resolution:** Use `docker ps -a` to locate stopped/hidden containers, and `docker rm -f <container_name>` to free up the namespace before initializing a new environment.