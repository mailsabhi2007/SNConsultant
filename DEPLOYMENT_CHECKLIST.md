# Deployment Checklist

Use this checklist to ensure a smooth deployment.

## Pre-Deployment

### Code Preparation
- [ ] All code committed to Git
- [ ] `.gitignore` includes sensitive files (`.env`, `chroma_db`, etc.)
- [ ] No hardcoded credentials in code
- [ ] All tests passing (if applicable)
- [ ] Documentation updated

### Environment Setup
- [ ] `.env.example` file created with template
- [ ] All required API keys obtained:
  - [ ] Anthropic API key
  - [ ] OpenAI API key
  - [ ] Tavily API key
- [ ] ServiceNow credentials ready (if using live instance)
- [ ] Environment variables documented

### Security
- [ ] `.env` file in `.gitignore`
- [ ] No API keys in code or config files
- [ ] Secrets management plan in place
- [ ] HTTPS configured (for production)
- [ ] Access controls planned

## Deployment Steps

### Streamlit Cloud
- [ ] Repository pushed to GitHub
- [ ] Streamlit Cloud account created
- [ ] App created in Streamlit Cloud
- [ ] Secrets configured in Streamlit Cloud dashboard
- [ ] Deployment successful
- [ ] App accessible via URL

### Docker
- [ ] Dockerfile created and tested
- [ ] `.dockerignore` configured
- [ ] `docker-compose.yml` created (if using)
- [ ] Image builds successfully
- [ ] Container runs without errors
- [ ] Environment variables passed correctly
- [ ] Volumes mounted correctly
- [ ] Health check working

### Cloud Platform (AWS/Azure/GCP)
- [ ] Cloud account set up
- [ ] Resource group/project created
- [ ] Compute resources provisioned
- [ ] Network security configured
- [ ] Environment variables set
- [ ] Application deployed
- [ ] Domain/DNS configured (if applicable)

## Post-Deployment

### Verification
- [ ] Application starts without errors
- [ ] All pages/tabs load correctly
- [ ] API connections working:
  - [ ] Anthropic API (Claude)
  - [ ] OpenAI API (embeddings)
  - [ ] Tavily API (search)
- [ ] ServiceNow connection tested (if configured)
- [ ] Knowledge base accessible
- [ ] File upload works
- [ ] Chat interface functional

### Functionality Tests
- [ ] Can ask questions and get responses
- [ ] Public docs search works
- [ ] Knowledge base search works
- [ ] Live instance connection works (if configured)
- [ ] Rate limit handling works
- [ ] Error messages display correctly
- [ ] Connection health check works

### Performance
- [ ] Response times acceptable
- [ ] No memory leaks
- [ ] Resource usage within limits
- [ ] Concurrent users handled properly

### Monitoring
- [ ] Logging configured
- [ ] Error tracking set up
- [ ] Health checks working
- [ ] Alerts configured (if applicable)
- [ ] Analytics/monitoring dashboard accessible

### Security
- [ ] HTTPS enabled
- [ ] API keys secured
- [ ] No sensitive data exposed
- [ ] Access controls in place
- [ ] Regular backup plan in place

## Maintenance

### Regular Tasks
- [ ] Monitor API usage and costs
- [ ] Review and rotate API keys quarterly
- [ ] Update dependencies monthly
- [ ] Review logs weekly
- [ ] Backup data regularly
- [ ] Test disaster recovery plan

### Updates
- [ ] Version control for deployments
- [ ] Rollback plan documented
- [ ] Change management process
- [ ] User communication plan

## Troubleshooting

### Common Issues
- [ ] Port conflicts resolved
- [ ] Environment variable issues fixed
- [ ] API connection problems resolved
- [ ] Database/vector store issues fixed
- [ ] Memory/resource issues addressed

## Sign-Off

- [ ] All checklist items completed
- [ ] Application tested and verified
- [ ] Documentation reviewed
- [ ] Team notified of deployment
- [ ] Ready for production use

---

**Deployment Date:** _______________
**Deployed By:** _______________
**Deployment Method:** _______________
**Environment:** _______________
