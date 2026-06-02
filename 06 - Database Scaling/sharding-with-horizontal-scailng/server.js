import express from 'express';
import {Pool} from 'pg';

const app = express();
app.use(express.json());

// 1. Establish connection to shards
const shard0 = new Pool({
    host: '127.0.0.1', // Changed from 'localhost'
    port: 5432,
    user: 'postgres',
    password: 'password',
    database: 'userdb'
})

const shard1 = new Pool({
    host:'127.0.0.1',
    port: 5433, 
    user: 'postgres', 
    password: 'password',
    database: 'userdb'
})

 // 2. Routing logic (Brain)
 function getTargetShard(userId){
    const shardId = userId % 2;
    console.log(`Routing user ${userId} to Shard ${shardId}`);
    return shardId === 0 ? shard0 : shard1; 
 } 

 // 3. WRITE API
 app.post('/users', async(req, res)=>{
    const {id, name}= req.body;
    
    const targetDatabase = getTargetShard(id);
   
    try {
        // Create the table if it doesn't exist (just for testing purposes)
        await targetDatabase.query('CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY, name VARCHAR(100));');
        
        // Insert the data into the chosen shard
        await targetDatabase.query('INSERT INTO users (id, name) VALUES ($1, $2)', [id, name]);
        res.send(`Successfully saved ${name} to Shard ${id % 2}\n`);
    } catch (err) {
        res.status(500).send(err.message);    
        console.error('Error saving user:', err);
    }
 }) 

// 4. READ API
app.get('/users/:id', async(req, res)=>{
    const userId = parseInt(req.params.id);
    
    // API figures out which database has the data
    const targetDatabase = getTargetShard(userId);

    try {
        const result = await targetDatabase.query('SELECT * FROM users WHERE id = $1', [userId]);
        if (result.rows.length > 0) {
            res.json(result.rows[0]);
        } else {
            res.status(404).send("User not found");
        }
    } catch (err) {
        res.status(500).send(err.message);
        console.error('Error reading user:', err);
    }
})

app.listen(3000, ()=>{
    console.log('Server is running on port 3000');
})