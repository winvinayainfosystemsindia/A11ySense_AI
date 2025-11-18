import os
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import aiohttp
import json
from ..core.exceptions import LLMException
from ..utils.logger import setup_logger

@dataclass
class LLMInsight:
    url: str
    priority_issues: List[Dict[str, Any]]
    productivity_impact: Dict[str, Any]
    code_recommendations: List[Dict[str, str]]
    business_impact: Dict[str, Any]
    roi_calculation: Dict[str, float]

class GroqClient:
    def __init__(self, config: dict):
        self.config = config.get('llm', {})
        self.api_key = self.config.get('api_key')
        self.model = self.config.get('model', 'llama3-70b-8192')
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.logger = setup_logger(__name__)
        
        if not self.api_key or self.api_key.startswith('${'):
            self.logger.warning("Groq API key not configured. LLM features will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
    
    async def generate_accessibility_insights(self, 
                                           analysis_results: List[AdvancedAccessibilityResult]) -> List[LLMInsight]:
        """Generate advanced insights using LLM"""
        if not self.enabled:
            self.logger.warning("LLM features are disabled. Returning empty insights.")
            return []
        
        insights = []
        
        for result in analysis_results:
            try:
                insight = await self._analyze_single_result(result)
                insights.append(insight)
            except Exception as e:
                self.logger.error(f"LLM analysis failed for {result.url}: {e}")
                # Create a basic insight even if LLM fails
                insights.append(self._create_basic_insight(result))
        
        return insights
    
    async def _analyze_single_result(self, result: AdvancedAccessibilityResult) -> LLMInsight:
        """Analyze single accessibility result using LLM"""
        
        prompt = self._build_productivity_prompt(result)
        
        response = await self._make_llm_request(prompt)
        
        return self._parse_llm_response(response, result.url)
    
    def _build_productivity_prompt(self, result: AdvancedAccessibilityResult) -> str:
        """Build productivity-focused prompt for LLM"""
        
        violations_summary = "\n".join([
            f"- {v['id']}: {v['description']} (Impact: {v.get('impact', 'unknown')})"
            for v in result.violations[:10]  # Limit to top 10 violations
        ])
        
        unique_insights = json.dumps(result.unique_insights, indent=2)
        
        prompt = f"""
        As an expert accessibility consultant focused on USER PRODUCTIVITY, analyze this accessibility audit and provide actionable insights.

        WEBSITE: {result.url}

        ACCESSIBILITY VIOLATIONS:
        {violations_summary}

        UNIQUE PRODUCTIVITY INSIGHTS:
        {unique_insights}

        Please analyze this data and provide:

        1. PRIORITY ISSUES (Top 3-5 issues that most impact user productivity):
           - Focus on navigation efficiency, task completion time, and cognitive load
           - Explain how each issue affects different user groups (keyboard-only, screen reader, low vision)

        2. PRODUCTIVITY IMPACT ASSESSMENT:
           - Estimated time loss per task due to accessibility barriers
           - Comparison to industry benchmarks for efficient interfaces
           - Specific user workflows that are most affected

        3. CODE RECOMMENDATIONS (Provide actual code fixes):
           - Specific, implementable code solutions
           - Focus on fixes that provide the biggest productivity gains
           - Include both HTML and JavaScript solutions where applicable

        4. BUSINESS IMPACT ANALYSIS:
           - How these issues affect conversion rates and user retention
           - Legal compliance risks and potential cost savings from fixes
           - Impact on different user segments (age, ability, device usage)

        5. ROI CALCULATION:
           - Estimated development time vs productivity gains
           - Priority ranking based on impact/effort ratio

        Format your response as JSON with this structure:
        {{
            "priority_issues": [
                {{
                    "issue": "issue name",
                    "productivity_impact": "description",
                    "user_groups_affected": ["group1", "group2"],
                    "estimated_time_loss": "X seconds per interaction"
                }}
            ],
            "productivity_impact": {{
                "overall_score": 0-100,
                "key_workflows_affected": ["workflow1", "workflow2"],
                "comparison_to_benchmark": "description"
            }},
            "code_recommendations": [
                {{
                    "issue": "issue name",
                    "html_fix": "code example",
                    "javascript_fix": "code example if needed",
                    "explanation": "why this improves productivity"
                }}
            ],
            "business_impact": {{
                "conversion_impact": "description",
                "legal_risks": ["risk1", "risk2"],
                "user_retention_impact": "description"
            }},
            "roi_calculation": {{
                "high_priority_fixes": ["fix1", "fix2"],
                "estimated_development_hours": X,
                "estimated_productivity_gain": "X%"
            }}
        }}

        Focus on practical, implementable advice that will genuinely improve user productivity.
        """
        
        return prompt
    
    async def _make_llm_request(self, prompt: str) -> str:
        """Make request to Groq API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert accessibility consultant specializing in user productivity and efficiency. Provide practical, actionable advice with specific code examples."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.config.get('temperature', 0.3),
            "max_tokens": self.config.get('max_tokens', 4000),
            "top_p": 1
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.base_url, headers=headers, json=payload, timeout=60) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['choices'][0]['message']['content']
                    else:
                        error_text = await response.text()
                        raise LLMException(f"Groq API error {response.status}: {error_text}")
            except asyncio.TimeoutError:
                raise LLMException("Groq API request timed out")
            except Exception as e:
                raise LLMException(f"Groq API request failed: {e}")
    
    def _parse_llm_response(self, response: str, url: str) -> LLMInsight:
        """Parse LLM response into structured insight"""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            
            data = json.loads(json_str)
            
            return LLMInsight(
                url=url,
                priority_issues=data.get('priority_issues', []),
                productivity_impact=data.get('productivity_impact', {}),
                code_recommendations=data.get('code_recommendations', []),
                business_impact=data.get('business_impact', {}),
                roi_calculation=data.get('roi_calculation', {})
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse LLM response: {e}")
            # Return basic insight structure
            return self._create_basic_insight_from_response(response, url)
    
    def _create_basic_insight(self, result: AdvancedAccessibilityResult) -> LLMInsight:
        """Create basic insight when LLM is disabled or fails"""
        return LLMInsight(
            url=result.url,
            priority_issues=[],
            productivity_impact={},
            code_recommendations=[],
            business_impact={},
            roi_calculation={}
        )
    
    def _create_basic_insight_from_response(self, response: str, url: str) -> LLMInsight:
        """Create basic insight from failed LLM response parsing"""
        return LLMInsight(
            url=url,
            priority_issues=[{"issue": "Parse Error", "description": "Failed to parse LLM response"}],
            productivity_impact={"overall_score": 0},
            code_recommendations=[],
            business_impact={},
            roi_calculation={}
        )