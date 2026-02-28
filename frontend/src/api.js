import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * 分析Python代码
 */
export const analyzeCode = async (code, options = {}) => {
  const response = await api.post('/api/analyze', {
    code,
    options,
  });
  return response.data;
};

/**
 * 获取AST图结构
 */
export const getAST = async (code, format = 'cytoscape', theme = 'default') => {
  const response = await api.post('/api/ast', {
    code,
    options: { format, theme },
  });
  return response.data;
};

/**
 * 获取复杂度分析
 */
export const getComplexity = async (code) => {
  const response = await api.post('/api/complexity', { code });
  return response.data;
};

/**
 * 获取性能问题
 */
export const getPerformanceIssues = async (code) => {
  const response = await api.post('/api/performance', { code });
  return response.data;
};

/**
 * 获取安全问题
 */
export const getSecurityIssues = async (code) => {
  const response = await api.post('/api/security', { code });
  return response.data;
};

/**
 * 获取优化建议
 */
export const getSuggestions = async (code) => {
  const response = await api.post('/api/suggestions', { code });
  return response.data;
};

/**
 * 生成补丁
 */
export const generatePatches = async (code) => {
  const response = await api.post('/api/patches', { code });
  return response.data;
};

/**
 * 获取节点解释（学习模式）
 */
export const explainNode = async (nodeId, code) => {
  const response = await api.post(`/api/learn/node/${nodeId}`, { code });
  return response.data;
};

/**
 * 获取挑战列表
 */
export const getChallenges = async () => {
  const response = await api.get('/api/challenges');
  return response.data;
};

/**
 * 获取挑战详情
 */
export const getChallenge = async (challengeId) => {
  const response = await api.get(`/api/challenges/${challengeId}`);
  return response.data;
};

/**
 * 提交挑战答案
 */
export const submitChallenge = async (challengeId, foundIssues) => {
  const response = await api.post('/api/challenges/submit', {
    challenge_id: challengeId,
    found_issues: foundIssues,
  });
  return response.data;
};

export default api;
