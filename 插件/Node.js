// server.js - 使用Express创建代理
const express = require('express');
const axios = require('axios');
const cors = require('cors');
const app = express();

app.use(cors());
app.use(express.json());

app.post('/api/analyze', async (req, res) => {
    try {
        const { prompt } = req.body;

        const response = await axios.post(
            `https://dashscope.aliyuncs.com/api/v1/apps/${process.env.APP_ID}/completion`,
            {
                input: { prompt },
                parameters: {},
                debug: {}
            },
            {
                headers: {
                    'Authorization': `Bearer ${process.env.API_KEY}`,
                    'Content-Type': 'application/json'
                }
            }
        );

        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});