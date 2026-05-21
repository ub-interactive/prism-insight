## Preparation Questions

Please answer these:

1. **Which market flow do you want first?**  
   - US only  

2. **What do you want to run initially?**  
   - Analysis only (no real orders)  

3. **Optional mobile push hooks** (`FIREBASE_BRIDGE_ENABLED`) — enable only after wiring PRISM-Mobile?  
   - Skip for now

4. **LLM auth mode** (`PRISM_OPENAI_AUTH_MODE`)  
   - `api_key`  (using deepseek openai compatible mode, api key see below)

5. **Do you already have these files ready?**  
   - `.env`  missing
   - `mcp_agent.secrets.yaml`  missing
   - `mcp_agent.config.yaml`  missing
   - `trading/config/kis_devlp.yaml`  missing

6. **US sentiment (optional):** do you want Adanos enabled?  
   - Yes  (you need to claim api key through their api)

7. **Multi-account trading setup?**  
   - Single account  

8. **Your OS Python command works as:**  
   - `python3`  

9. **Do you want me to optimize for “quick local test” first?**  
   - Yes (fastest local validation path)


## LLM

deepseek api key: [REDACTED - rotate this key before use]