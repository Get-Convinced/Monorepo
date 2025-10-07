"""
LLM service for OpenAI integration with RAG support.

This service handles OpenAI API interactions, prompt building,
and token counting for chat completion generation.
"""

import logging
import os
import time
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI, OpenAIError
import tiktoken

from ..models.chat import ResponseMode

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Base exception for LLM service errors."""
    pass


class TokenLimitExceededError(LLMServiceError):
    """Token limit exceeded for the model."""
    pass


class LLMService:
    """Service for OpenAI LLM interactions."""
    
    # Temperature mapping for response modes
    TEMPERATURE_MAP = {
        ResponseMode.STRICT: 0.1,
        ResponseMode.BALANCED: 0.5,
        ResponseMode.CREATIVE: 0.9
    }
    
    # Model token limits
    MODEL_TOKEN_LIMITS = {
        "gpt-4o": 128000,
        "gpt-3.5-turbo": 16385
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM service.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            
        Raises:
            ValueError: If API key is not provided
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY required")
        
        self.client = AsyncOpenAI(api_key=self.api_key, max_retries=0, timeout=30.0)
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
        logger.info("LLM service initialized")
    
    def _build_system_prompt(self, mode: ResponseMode) -> str:
        """
        Build system prompt based on response mode.
        
        Args:
            mode: Response generation mode
            
        Returns:
            System prompt string
        """
        base_prompt = """You are a helpful AI assistant that answers questions based on provided document context.

Instructions:
- Use ONLY the information from the provided context to answer questions
- Cite sources by referring to document names when possible
- Be accurate and precise
"""
        
        if mode == ResponseMode.STRICT:
            return base_prompt + """- If the context doesn't contain enough information, say "I don't have enough information to answer that."
- Do not make assumptions or infer beyond what's explicitly stated"""
        
        elif mode == ResponseMode.BALANCED:
            return base_prompt + """- If the context is insufficient, clearly state what information is missing
- You may make reasonable inferences if they're logical and clearly stated"""
        
        else:  # CREATIVE
            return base_prompt + """- Feel free to provide broader context and make reasonable inferences
- You may elaborate on topics using your general knowledge when helpful
- Always indicate when you're providing information beyond the source documents"""
    
    def _format_context(self, chunks: List[Dict[str, Any]], numbered: bool = False) -> str:
        """
        Format Ragie chunks into context string.
        
        Args:
            chunks: List of document chunks with metadata
            numbered: If True, include source numbers for function calling
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant documents found."
        
        context_parts = ["Relevant document excerpts:\n"]
        for i, chunk in enumerate(chunks, 1):
            doc_name = chunk.get("document_name", "Unknown")
            page = chunk.get("page_number")
            text = chunk.get("text", "")
            score = chunk.get("score", 0)
            
            page_info = f", Page {page}" if page else ""
            context_parts.append(
                f"\n[Source {i}] {doc_name}{page_info} (Relevance: {score:.2f})\n{text}\n"
            )
        
        return "\n".join(context_parts)
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))
    
    async def generate_response_with_sources(
        self,
        question: str,
        chunks: List[Dict[str, Any]],
        mode: ResponseMode = ResponseMode.STRICT,
        model: str = "gpt-4o",
        conversation_history: Optional[List[Dict[str, str]]] = None,
        use_function_calling: bool = True
    ) -> Dict[str, Any]:
        """
        Generate response with structured source tracking using OpenAI function calling.
        
        Args:
            question: User question
            chunks: Retrieved document chunks
            mode: Response generation mode
            model: OpenAI model to use
            conversation_history: Previous messages for context
            use_function_calling: Use function calling for structured output
            
        Returns:
            Dict with response content, sources_used, token usage, and metadata
            
        Raises:
            LLMServiceError: If generation fails
        """
        start_time = time.time()
        
        try:
            # Build messages
            system_prompt = self._build_system_prompt(mode) + """

When answering, you MUST use the respond_with_sources function to provide:
1. Your answer in markdown format
2. A list of sources you actually used, with the source number and why you used it

Only include sources that directly contributed to your answer."""
            
            context = self._format_context(chunks, numbered=True)
            temperature = self.TEMPERATURE_MAP[mode]
            
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (last 5 messages)
            if conversation_history:
                messages.extend(conversation_history[-5:])
            
            # Add current question with context
            user_message = f"{context}\n\nQuestion: {question}"
            messages.append({"role": "user", "content": user_message})
            
            # Define function for structured output
            functions = [{
                "name": "respond_with_sources",
                "description": "Respond to the user's question with source citations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Your answer in markdown format"
                        },
                        "sources_used": {
                            "type": "array",
                            "description": "List of sources actually used in your answer",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "source_num": {
                                        "type": "integer",
                                        "description": "Source number from the context (1-based)"
                                    },
                                    "reason": {
                                        "type": "string",
                                        "description": "Brief explanation of why you used this source"
                                    }
                                },
                                "required": ["source_num", "reason"]
                            }
                        }
                    },
                    "required": ["message", "sources_used"]
                }
            }]
            
            # Check token limit
            total_prompt_tokens = sum(self.count_tokens(str(msg.get("content", ""))) for msg in messages)
            model_limit = self.MODEL_TOKEN_LIMITS.get(model, 16385)
            
            if total_prompt_tokens > model_limit - 1500:
                raise TokenLimitExceededError(
                    f"Prompt tokens ({total_prompt_tokens}) exceed model limit ({model_limit})"
                )
            
            logger.info(
                "Generating LLM response with function calling",
                extra={
                    "model": model,
                    "mode": mode.value,
                    "temperature": temperature,
                    "chunks_count": len(chunks),
                    "use_function_calling": use_function_calling
                }
            )
            
            # Call OpenAI with function calling
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                functions=functions if use_function_calling else None,
                function_call={"name": "respond_with_sources"} if use_function_calling else None,
                temperature=temperature,
                max_tokens=1500,
                stream=False,
                timeout=30.0
            )
            
            choice = response.choices[0]
            usage = response.usage
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Parse function call response
            if use_function_calling and choice.message.function_call:
                import json
                try:
                    function_args = json.loads(choice.message.function_call.arguments)
                    content = function_args.get("message", "")
                    sources_used = function_args.get("sources_used", [])
                    
                    logger.info(
                        "LLM response generated with sources",
                        extra={
                            "tokens_total": usage.total_tokens,
                            "sources_used_count": len(sources_used),
                            "processing_time_ms": processing_time_ms
                        }
                    )
                    
                    return {
                        "content": content,
                        "sources_used": sources_used,
                        "tokens_prompt": usage.prompt_tokens,
                        "tokens_completion": usage.completion_tokens,
                        "tokens_total": usage.total_tokens,
                        "model": model,
                        "temperature": temperature,
                        "processing_time_ms": processing_time_ms,
                        "used_function_calling": True
                    }
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to parse function call response: {e}. Retrying without function calling.")
                    # Fallback: retry without function calling
                    return await self.generate_response_with_sources(
                        question=question,
                        chunks=chunks,
                        mode=mode,
                        model=model,
                        conversation_history=conversation_history,
                        use_function_calling=False
                    )
            else:
                # Fallback: use plain text response
                content = choice.message.content or ""
                logger.info(
                    "LLM response generated (no function calling)",
                    extra={
                        "tokens_total": usage.total_tokens,
                        "processing_time_ms": processing_time_ms
                    }
                )
                
                return {
                    "content": content,
                    "sources_used": [],  # Empty - mark all as potentially used
                    "tokens_prompt": usage.prompt_tokens,
                    "tokens_completion": usage.completion_tokens,
                    "tokens_total": usage.total_tokens,
                    "model": model,
                    "temperature": temperature,
                    "processing_time_ms": processing_time_ms,
                    "used_function_calling": False
                }
            
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMServiceError(f"LLM generation failed: {e}")
        except TokenLimitExceededError:
            raise
        except Exception as e:
            logger.error(f"Unexpected LLM error: {e}")
            raise LLMServiceError(f"Unexpected error: {e}")
    
    async def generate_response(
        self,
        question: str,
        chunks: List[Dict[str, Any]],
        mode: ResponseMode = ResponseMode.STRICT,
        model: str = "gpt-4o",
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate response using OpenAI.
        
        Args:
            question: User question
            chunks: Retrieved document chunks
            mode: Response generation mode
            model: OpenAI model to use
            conversation_history: Previous messages for context
            
        Returns:
            Dict with response content, token usage, and metadata
            
        Raises:
            LLMServiceError: If generation fails
            TokenLimitExceededError: If token limit is exceeded
        """
        start_time = time.time()
        
        try:
            # Build messages
            system_prompt = self._build_system_prompt(mode)
            context = self._format_context(chunks)
            temperature = self.TEMPERATURE_MAP[mode]
            
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (last 5 messages)
            if conversation_history:
                messages.extend(conversation_history[-5:])
            
            # Add current question with context
            user_message = f"{context}\n\nQuestion: {question}"
            messages.append({"role": "user", "content": user_message})
            
            # Check token limit
            total_prompt_tokens = sum(self.count_tokens(str(msg.get("content", ""))) for msg in messages)
            model_limit = self.MODEL_TOKEN_LIMITS.get(model, 16385)
            
            if total_prompt_tokens > model_limit - 1500:  # Reserve 1500 for completion
                raise TokenLimitExceededError(
                    f"Prompt tokens ({total_prompt_tokens}) exceed model limit ({model_limit})"
                )
            
            logger.info(
                "Generating LLM response",
                extra={
                    "model": model,
                    "mode": mode.value,
                    "temperature": temperature,
                    "chunks_count": len(chunks),
                    "history_messages": len(conversation_history or []),
                    "prompt_tokens": total_prompt_tokens
                }
            )
            
            # Call OpenAI
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=1500,
                stream=False,
                timeout=30.0
            )
            
            content = response.choices[0].message.content
            usage = response.usage
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                "LLM response generated",
                extra={
                    "tokens_total": usage.total_tokens,
                    "processing_time_ms": processing_time_ms
                }
            )
            
            return {
                "content": content,
                "tokens_prompt": usage.prompt_tokens,
                "tokens_completion": usage.completion_tokens,
                "tokens_total": usage.total_tokens,
                "model": model,
                "temperature": temperature,
                "processing_time_ms": processing_time_ms
            }
            
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMServiceError(f"LLM generation failed: {e}")
        except TokenLimitExceededError:
            raise
        except Exception as e:
            logger.error(f"Unexpected LLM error: {e}")
            raise LLMServiceError(f"Unexpected error: {e}")


# Singleton instance to avoid repeated initialization
_llm_service_instance: Optional[LLMService] = None

def get_llm_service() -> LLMService:
    """
    Dependency to get LLM service instance (singleton).
    
    Returns:
        Configured LLM service
    """
    global _llm_service_instance
    
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
        logger.info("LLM service initialized")
    
    return _llm_service_instance
