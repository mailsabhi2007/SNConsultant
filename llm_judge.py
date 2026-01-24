"""LLM Judge for hallucination detection."""

import os
import json
from typing import Dict, Any, Optional, List
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from database import get_db_connection


class LLMJudge:
    """Judge LLM for detecting hallucinations in main LLM responses."""
    
    def __init__(self, model_name: Optional[str] = None, provider: Optional[str] = None):
        """
        Initialize the judge LLM.
        
        Args:
            model_name: Model to use for judging
            provider: "openai" or "anthropic" (auto-detected from model name if not provided)
        
        Supported models:
        OpenAI:
        - gpt-4o (recommended for best quality)
        - gpt-4o-mini (recommended for cost-effectiveness)
        - gpt-4-turbo
        - gpt-3.5-turbo
        
        Anthropic:
        - claude-sonnet-4-20250514 (current, recommended)
        - claude-3-5-sonnet-20240620 (deprecated, retired Oct 2025)
        """
        # Determine provider and model
        judge_provider = provider or os.getenv("JUDGE_PROVIDER", "").lower()
        default_model = os.getenv("JUDGE_MODEL", "gpt-4o-mini")  # Default to GPT for cost-effectiveness
        
        self.model_name = model_name or default_model
        
        # Auto-detect provider from model name if not specified
        if not judge_provider:
            if self.model_name.startswith("gpt") or self.model_name.startswith("o1"):
                judge_provider = "openai"
            elif "claude" in self.model_name.lower():
                judge_provider = "anthropic"
            else:
                # Default to OpenAI if unclear
                judge_provider = "openai"
        
        self.provider = judge_provider
        self.judge_model: Optional[BaseChatModel] = None
        
        # Initialize based on provider
        if self.provider == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError(
                    "OPENAI_API_KEY environment variable is not set. "
                    "Please add it to your .env file or set JUDGE_PROVIDER=anthropic to use Claude."
                )
            
            try:
                self.judge_model = ChatOpenAI(
                    model=self.model_name,
                    temperature=0,  # Deterministic judging
                )
            except Exception as e:
                # Try fallback to gpt-4o-mini if specified model fails
                if self.model_name != "gpt-4o-mini":
                    print(f"Warning: Failed to initialize judge model {self.model_name}: {e}")
                    print("Attempting fallback to: gpt-4o-mini")
                    try:
                        self.model_name = "gpt-4o-mini"
                        self.judge_model = ChatOpenAI(
                            model=self.model_name,
                            temperature=0,
                        )
                    except Exception as fallback_error:
                        raise ValueError(
                            f"Failed to initialize OpenAI judge model. Tried {model_name or 'default'} and gpt-4o-mini. "
                            f"Error: {fallback_error}. Please check your OPENAI_API_KEY and model name."
                        )
                else:
                    raise ValueError(
                        f"Failed to initialize OpenAI judge model {self.model_name}. "
                        f"Error: {e}. Please check your OPENAI_API_KEY."
                    )
        
        elif self.provider == "anthropic":
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable is not set. "
                    "Please add it to your .env file or set JUDGE_PROVIDER=openai to use GPT."
                )
            
            try:
                self.judge_model = ChatAnthropic(
                    model=self.model_name,
                    temperature=0,  # Deterministic judging
                )
            except Exception as e:
                # Try fallback model if initialization fails
                print(f"Warning: Failed to initialize judge model {self.model_name}: {e}")
                fallback_model = "claude-3-5-sonnet-20240620" if "sonnet-4" in self.model_name else "claude-sonnet-4-20250514"
                print(f"Attempting fallback to: {fallback_model}")
                try:
                    self.model_name = fallback_model
                    self.judge_model = ChatAnthropic(
                        model=self.model_name,
                        temperature=0,
                    )
                except Exception as fallback_error:
                    raise ValueError(
                        f"Failed to initialize Anthropic judge model. Tried {model_name or 'default'} and {fallback_model}. "
                        f"Error: {fallback_error}. Please check your ANTHROPIC_API_KEY and model name."
                    )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}. Use 'openai' or 'anthropic'.")
        
        self.system_prompt = """You are an expert fact-checker and hallucination detector for AI-generated responses about ServiceNow.

Your task is to evaluate whether a response from the main AI assistant contains hallucinations, inaccuracies, or unsupported claims.

A hallucination is:
- Information that contradicts the provided sources
- Claims not supported by any source
- Fabricated details, numbers, or facts
- Incorrect technical specifications
- Made-up URLs, table names, or API endpoints

You will receive:
1. The user's original query
2. The assistant's response
3. The sources/citations that were used (if any)
4. Any relevant context from knowledge base searches

Evaluate the response and provide:
1. A hallucination score from 0.0 to 1.0 (where 1.0 = high confidence of hallucination)
2. Whether it's a hallucination (true/false) - use threshold of 0.7
3. Specific sections that are problematic (if any)
4. Suggested corrections (if any)
5. Your reasoning

Be strict but fair. Only flag clear hallucinations, not minor imprecisions or stylistic differences."""

    def evaluate_response(
        self,
        user_query: str,
        assistant_response: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        knowledge_base_results: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a response for hallucinations.
        
        Args:
            user_query: Original user query
            assistant_response: The assistant's response to evaluate
            sources: List of sources/citations used (optional)
            knowledge_base_results: Results from knowledge base search (optional)
            
        Returns:
            Dictionary with evaluation results:
            - hallucination_score: float (0.0-1.0)
            - is_hallucination: bool
            - flagged_sections: List[str]
            - suggested_corrections: List[str]
            - reasoning: str
        """
        # Build evaluation prompt
        evaluation_prompt = f"""Evaluate the following AI response for hallucinations.

USER QUERY:
{user_query}

ASSISTANT RESPONSE:
{assistant_response}
"""
        
        if sources:
            evaluation_prompt += f"\n\nSOURCES/CITATIONS USED:\n"
            for i, source in enumerate(sources, 1):
                evaluation_prompt += f"{i}. {source}\n"
        
        if knowledge_base_results:
            evaluation_prompt += f"\n\nKNOWLEDGE BASE RESULTS:\n"
            for i, result in enumerate(knowledge_base_results, 1):
                evaluation_prompt += f"{i}. Source: {result.get('source', 'Unknown')}\n"
                evaluation_prompt += f"   Content: {result.get('content', '')[:500]}...\n"
        
        evaluation_prompt += """
\nPlease evaluate this response and provide your assessment in the following JSON format:
{
    "hallucination_score": 0.0-1.0,
    "is_hallucination": true/false,
    "flagged_sections": ["section 1", "section 2"],
    "suggested_corrections": ["correction 1", "correction 2"],
    "reasoning": "Your detailed reasoning here"
}
"""
        
        try:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=evaluation_prompt)
            ]
            
            try:
                response = self.judge_model.invoke(messages)
                response_text = response.content
            except Exception as api_error:
                # Handle API errors (404, rate limits, etc.)
                error_str = str(api_error)
                error_details = {
                    'hallucination_score': 0.5,
                    'is_hallucination': False,
                    'flagged_sections': [],
                    'suggested_corrections': [],
                    'reasoning': f"Error during evaluation: {error_str}. The judge model '{self.model_name}' may be unavailable or incorrect. Please check your model name and API key.",
                    'judge_model': self.model_name,
                    'error': True,
                    'error_type': type(api_error).__name__
                }
                
                # Log the error for debugging
                try:
                    import traceback
                    print(f"Judge API Error: {error_str}")
                    print(traceback.format_exc())
                except:
                    pass
                
                return error_details
            
            # Try to extract JSON from response
            # The model might wrap JSON in markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            # Parse JSON response
            evaluation = json.loads(response_text)
            
            # Ensure all required fields
            result = {
                'hallucination_score': float(evaluation.get('hallucination_score', 0.0)),
                'is_hallucination': bool(evaluation.get('is_hallucination', False)),
                'flagged_sections': evaluation.get('flagged_sections', []),
                'suggested_corrections': evaluation.get('suggested_corrections', []),
                'reasoning': evaluation.get('reasoning', 'No reasoning provided'),
                'judge_model': self.model_name
            }
            
            return result
            
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            return {
                'hallucination_score': 0.5,  # Unknown - flag for review
                'is_hallucination': False,
                'flagged_sections': [],
                'suggested_corrections': [],
                'reasoning': f"Error parsing judge response: {str(e)}. Original response: {response_text[:200]}",
                'judge_model': self.model_name,
                'error': True
            }
        except Exception as e:
            # Catch any other unexpected errors
            error_str = str(e)
            error_type = type(e).__name__
            
            # Provide more helpful error messages
            if "404" in error_str or "not_found" in error_str.lower():
                if self.provider == "openai":
                    error_msg = f"Model '{self.model_name}' not found. Please check the model name. Try 'gpt-4o', 'gpt-4o-mini', or 'gpt-4-turbo'."
                else:
                    error_msg = f"Model '{self.model_name}' not found. Please check the model name. Try 'claude-sonnet-4-20250514' or 'claude-3-5-sonnet-20240620'."
            elif "401" in error_str or "unauthorized" in error_str.lower():
                api_key_name = "OPENAI_API_KEY" if self.provider == "openai" else "ANTHROPIC_API_KEY"
                error_msg = f"Authentication failed. Please check your {api_key_name}."
            elif "rate_limit" in error_str.lower() or "429" in error_str:
                error_msg = f"Rate limit exceeded. Please try again later."
            else:
                error_msg = f"Error during evaluation: {error_str}"
            
            # Log the error for debugging
            try:
                import traceback
                print(f"Judge Evaluation Error ({error_type}): {error_str}")
                print(traceback.format_exc())
            except:
                pass
            
            return {
                'hallucination_score': 0.5,
                'is_hallucination': False,
                'flagged_sections': [],
                'suggested_corrections': [],
                'reasoning': error_msg,
                'judge_model': self.model_name,
                'error': True,
                'error_type': error_type
            }

    def save_evaluation(
        self,
        message_id: int,
        evaluation: Dict[str, Any]
    ) -> int:
        """
        Save evaluation results to database.
        
        Args:
            message_id: ID of the message that was evaluated
            evaluation: Evaluation result dictionary
            
        Returns:
            check_id
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            flagged_sections_str = json.dumps(evaluation.get('flagged_sections', []))
            corrections_str = json.dumps(evaluation.get('suggested_corrections', []))
            
            cursor.execute("""
                INSERT INTO hallucination_checks (
                    message_id, judge_model, hallucination_score,
                    is_hallucination, flagged_sections, suggested_corrections,
                    judge_reasoning
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                message_id,
                evaluation.get('judge_model', 'unknown'),
                evaluation.get('hallucination_score', 0.0),
                evaluation.get('is_hallucination', False),
                flagged_sections_str,
                corrections_str,
                evaluation.get('reasoning', '')
            ))
            
            return cursor.lastrowid

    def get_evaluation(self, message_id: int) -> Optional[Dict[str, Any]]:
        """Get evaluation for a message."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT check_id, judge_model, hallucination_score, is_hallucination,
                       flagged_sections, suggested_corrections, judge_reasoning, created_at
                FROM hallucination_checks
                WHERE message_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (message_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                'check_id': row[0],
                'judge_model': row[1],
                'hallucination_score': row[2],
                'is_hallucination': bool(row[3]),
                'flagged_sections': json.loads(row[4]) if row[4] else [],
                'suggested_corrections': json.loads(row[5]) if row[5] else [],
                'reasoning': row[6],
                'created_at': row[7]
            }


# Global judge instance
_judge_instance = None


def get_judge(force_recreate: bool = False) -> LLMJudge:
    """
    Get or create the judge instance.
    
    Args:
        force_recreate: If True, recreate the judge instance even if one exists.
                       Useful when model configuration changes.
    """
    global _judge_instance
    
    # Check if existing instance uses old/invalid model
    if _judge_instance is not None:
        if hasattr(_judge_instance, 'model_name'):
            # Check if it's using the old invalid model
            if "claude-sonnet-3-5-20241022" in _judge_instance.model_name:
                print(f"Warning: Judge instance using old model '{_judge_instance.model_name}'. Recreating with GPT default.")
                _judge_instance = None  # Force recreation
                force_recreate = True
    
    # Check if we need to recreate (e.g., if model config changed)
    if force_recreate or _judge_instance is None:
        # Check for environment variable override
        env_model = os.getenv("JUDGE_MODEL", "")
        env_provider = os.getenv("JUDGE_PROVIDER", "").lower()
        
        # If old Claude model is specified, warn and use GPT instead
        if env_model and "claude-sonnet-3-5-20241022" in env_model:
            print(f"Warning: Environment variable JUDGE_MODEL set to old model '{env_model}'. Using GPT default instead.")
            env_model = ""  # Clear to use default
            env_provider = ""  # Clear to auto-detect
        
        # Create new instance
        try:
            _judge_instance = LLMJudge(
                model_name=env_model if env_model else None,
                provider=env_provider if env_provider else None
            )
            # Verify it's not using the old model
            if hasattr(_judge_instance, 'model_name') and "claude-sonnet-3-5-20241022" in _judge_instance.model_name:
                print(f"Error: Judge still initialized with old model. Forcing GPT default.")
                _judge_instance = LLMJudge(model_name="gpt-4o-mini", provider="openai")
        except Exception as e:
            # If initialization fails, try GPT as fallback
            print(f"Warning: Judge initialization failed: {e}. Falling back to GPT.")
            try:
                _judge_instance = LLMJudge(model_name="gpt-4o-mini", provider="openai")
            except Exception as fallback_error:
                print(f"Error: Failed to initialize judge with GPT fallback: {fallback_error}")
                raise
    
    return _judge_instance


def reset_judge():
    """Force reset the global judge instance. Useful when configuration changes."""
    global _judge_instance
    _judge_instance = None
