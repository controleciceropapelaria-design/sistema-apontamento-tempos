# 🔑 Configuração do GitHub Token para Streamlit Cloud

## 📋 Passo a Passo:

### 1️⃣ Criar Token no GitHub
1. Acesse: https://github.com/settings/tokens
2. Clique em **"Generate new token"** → **"Generate new token (classic)"**
3. Configure o token:
   - **Name:** `Sistema Apontamento Tempos`
   - **Expiration:** `No expiration` (ou 1 year)
   - **Scopes:** Marque apenas **`repo`** (acesso completo aos repositórios)
4. Clique em **"Generate token"**
5. **IMPORTANTE:** Copie o token gerado (começa com `ghp_`)

### 2️⃣ Configurar no Streamlit Cloud
1. Acesse seu app no Streamlit Cloud
2. Vá em **Settings** → **Secrets**
3. Cole o seguinte conteúdo:

```toml
GITHUB_TOKEN = "ghp_seu_token_aqui_substituir_por_token_real"
```

4. Clique em **"Save"**
5. O app será reiniciado automaticamente

### 3️⃣ Verificar Funcionamento
- ✅ **Com token:** Aparece "🌐 Conectado ao GitHub"
- ❌ **Sem token:** Aparece "⚠️ Modo offline"

## 🚀 Arquivos para Deploy:

### Principal:
- **app_cloud.py** - Versão com GitHub API
- **requirements.txt** - Dependências atualizadas  

### Alternativos:
- **app_github.py** - Versão com Git local (só funciona local)

## 🔧 Troubleshooting:

### Token não funciona:
1. Verifique se copiou o token completo
2. Confirme que marcou scope **`repo`**
3. Token não pode estar expirado

### Erro de permissões:
- Confirme que o token tem acesso ao repositório
- Se repositório é privado, precisa de permissões extras

## 📝 Exemplo de secrets.toml:
```toml
GITHUB_TOKEN = "ghp_1234567890abcdef1234567890abcdef12345678"
```

**⚠️ NUNCA commitar o token real para o Git!**