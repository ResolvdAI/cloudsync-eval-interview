"""
Core Customer Support Agent implementation using LlamaIndex.
"""

from .prompts import SYSTEM_PROMPT, QUERY_PROMPT_TEMPLATE
from .tools import (
    BillingLookupTool,
    TicketCreationTool,
    SystemStatusTool,
)
from config.settings import settings
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.llms.anthropic import Anthropic
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool, ToolMetadata
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings as LlamaSettings,
    StorageContext,
    load_index_from_storage,
)
import copy
import functools
import inspect
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file FIRST
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class CustomerSupportAgent:
    """
    AI-powered customer support agent for CloudSync.

    This agent handles customer inquiries by leveraging:
    - A knowledge base of documents (FAQs, troubleshooting guides, etc.)
    - Custom tools for billing, ticket creation, and system status
    - LLM for natural language understanding (OpenAI by default, Anthropic supported)
    """

    def __init__(
        self,
        knowledge_base_path: Optional[str] = None,
        use_cached_index: bool = True,
        verbose: bool = False,
    ):
        """
        Initialize the Customer Support Agent.

        Args:
            knowledge_base_path: Path to knowledge base documents
            use_cached_index: Whether to use cached vector index if available
            verbose: Whether to print verbose output
        """
        self.verbose = verbose
        self._tool_calls: List[Dict[str, Any]] = []
        self.knowledge_base_path = knowledge_base_path or settings.knowledge_base_path
        self.index_storage_path = "storage/vector_index"

        if verbose:
            logger.setLevel(logging.DEBUG)
        logger.info(f"🚀 Initializing CustomerSupportAgent (verbose={verbose})")

        # Initialize LLM
        logger.info(f"🤖 Setting up LLM ({settings.llm_model})...")
        self._setup_llm()

        # Initialize knowledge base
        logger.info("📚 Loading knowledge base...")
        self.index = self._load_knowledge_base(use_cached_index)

        # Memory for conversation history
        logger.info("🧠 Setting up conversation memory...")
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=4096)

        # Initialize tools
        logger.info("🔧 Setting up agent tools...")
        self.tools = self._setup_tools()

        # Initialize agent
        logger.info("🎯 Creating ReAct agent...")
        self.agent = self._create_agent()
        logger.info("✅ Agent initialization complete!")

    def _setup_llm(self):
        """Configure the LLM and embedding models."""
        logger.debug(f"Using model: {settings.llm_model}")

        # Determine provider from model name
        model = settings.llm_model
        if model.startswith("claude"):
            if not settings.anthropic_api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable is not set")
            self.llm = Anthropic(
                model=model,
                api_key=settings.anthropic_api_key,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
            )
        else:
            if not settings.openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable is not set")
            self.llm = OpenAI(
                model=model,
                api_key=settings.openai_api_key,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
            )

        logger.debug(
            f"LLM configured with temperature={settings.temperature}, max_tokens={settings.max_tokens}")

        # Set up embeddings (using OpenAI for now)
        if settings.openai_api_key:
            self.embed_model = OpenAIEmbedding(
                model=settings.embedding_model,
                api_key=settings.openai_api_key,
            )
        else:
            # Fallback to default embedding model
            self.embed_model = None

        # Configure global settings
        LlamaSettings.llm = self.llm
        if self.embed_model:
            LlamaSettings.embed_model = self.embed_model
        LlamaSettings.chunk_size = settings.chunk_size
        LlamaSettings.chunk_overlap = settings.chunk_overlap

    def _load_knowledge_base(self, use_cached: bool = True) -> VectorStoreIndex:
        """
        Load or create the knowledge base vector index.

        Args:
            use_cached: Whether to use cached index if available

        Returns:
            VectorStoreIndex containing the knowledge base
        """
        # Check if cached index exists
        if use_cached and os.path.exists(self.index_storage_path):
            logger.info(
                f"📦 Loading cached vector index from {self.index_storage_path}")
            storage_context = StorageContext.from_defaults(
                persist_dir=self.index_storage_path
            )
            index = load_index_from_storage(storage_context)
            logger.info("✅ Cached index loaded successfully")
            return index

        # Create new index from documents
        logger.info(
            f"🔄 Creating new vector index from {self.knowledge_base_path}...")

        # Check if knowledge base path exists
        kb_path = Path(self.knowledge_base_path)
        if not kb_path.exists():
            if self.verbose:
                print(
                    f"Knowledge base path {kb_path} does not exist. Creating empty index...")
            # Create empty index
            return VectorStoreIndex.from_documents([])

        # Load documents
        logger.debug("Loading documents from knowledge base...")
        documents = SimpleDirectoryReader(
            self.knowledge_base_path,
            recursive=True,
            exclude_hidden=True,
        ).load_data()

        if not documents:
            logger.warning(
                "⚠️ No documents found in knowledge base. Creating empty index...")
            return VectorStoreIndex.from_documents([])

        logger.info(f"📄 Found {len(documents)} documents to index")

        # Create index
        index = VectorStoreIndex.from_documents(
            documents,
            show_progress=self.verbose
        )

        # Persist index for future use
        logger.debug(f"Persisting index to {self.index_storage_path}")
        index.storage_context.persist(persist_dir=self.index_storage_path)
        logger.info("✅ Vector index created and cached successfully")

        return index

    def _record_tool_call(self, name: str, arguments: Dict[str, Any]) -> None:
        """Record one real tool invocation, in call order."""
        try:
            arguments_snapshot = copy.deepcopy(arguments)
        except Exception:
            arguments_snapshot = dict(arguments)
        self._tool_calls.append({
            "order": len(self._tool_calls) + 1,
            "name": name,
            "arguments": arguments_snapshot,
        })

    def get_tool_trace(self) -> List[Dict[str, Any]]:
        """
        Return tool invocations recorded during the most recent query.

        Each entry contains:
        - order: 1-based position of the call within that query
        - name: tool name
        - arguments: arguments actually passed to the tool. Defaults the
          caller omitted are not filled in.

        The list is cleared at the start of each query. This is a copy of
        the recorded calls, not a reconstruction from the final answer.
        """
        return copy.deepcopy(self._tool_calls)

    def _traced_function_tool(
        self,
        fn: Any,
        name: str,
        description: str,
    ) -> FunctionTool:
        """Wrap a tool function so each invocation is appended to the trace."""
        signature = inspect.signature(fn)

        @functools.wraps(fn)
        def traced(*args: Any, **kwargs: Any) -> Any:
            try:
                arguments = dict(signature.bind(*args, **kwargs).arguments)
            except TypeError:
                arguments = dict(kwargs)
                for index, value in enumerate(args):
                    arguments[f"arg_{index}"] = value
            self._record_tool_call(name, arguments)
            return fn(*args, **kwargs)

        traced.__signature__ = signature  # type: ignore[attr-defined]
        return FunctionTool.from_defaults(
            fn=traced,
            name=name,
            description=description,
        )

    def _setup_tools(self) -> List[FunctionTool]:
        """
        Set up the agent's custom tools.

        Returns:
            List of FunctionTool instances
        """
        tools = []
        logger.debug("Initializing agent tools...")

        # Knowledge base query tool
        if self.index:
            logger.debug("📚 Adding knowledge base search tool")
            query_engine = self.index.as_query_engine(
                similarity_top_k=3,
                verbose=self.verbose
            )

            def search_knowledge_base(query: str) -> str:
                """Search general CloudSync product and troubleshooting facts."""
                return str(query_engine.query(query))

            tools.append(
                self._traced_function_tool(
                    search_knowledge_base,
                    name="search_knowledge_base",
                    description=(
                        "Search the CloudSync knowledge base for general product "
                        "and troubleshooting facts, including features, pricing, "
                        "setup, FAQs, and how to fix common problems. "
                        "Use this for product questions that are not about a "
                        "specific customer's billing, a current service issue, "
                        "or creating a support ticket."
                    ),
                )
            )

        # Billing lookup tool
        if settings.enable_billing_tool:
            logger.debug("💳 Adding billing lookup tool")
            billing_tool = BillingLookupTool()
            tools.append(
                self._traced_function_tool(
                    billing_tool.lookup,
                    name=billing_tool.name,
                    description=billing_tool.description,
                )
            )

        # Ticket creation tool
        if settings.enable_ticket_tool:
            logger.debug("🎫 Adding ticket creation tool")
            ticket_tool = TicketCreationTool()
            tools.append(
                self._traced_function_tool(
                    ticket_tool.create,
                    name=ticket_tool.name,
                    description=ticket_tool.description,
                )
            )

        # System status tool
        if settings.enable_status_tool:
            logger.debug("🔍 Adding system status tool")
            status_tool = SystemStatusTool()
            tools.append(
                self._traced_function_tool(
                    status_tool.check,
                    name=status_tool.name,
                    description=status_tool.description,
                )
            )

        logger.info(f"✅ Initialized {len(tools)} tools for agent")
        return tools

    def _create_agent(self) -> ReActAgent:
        """
        Create the ReAct agent with configured tools and prompts.

        Returns:
            Configured ReActAgent instance
        """
        # In newer versions of llama-index, use the constructor directly
        return ReActAgent(
            tools=self.tools,
            llm=self.llm,
            memory=self.memory,
            verbose=self.verbose,
            system_prompt=SYSTEM_PROMPT,
            max_iterations=10,
        )

    def query(self, user_query: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a customer query and return a response.

        Args:
            user_query: The customer's question or request
            metadata: Optional metadata about the query (customer_id, etc.)

        Returns:
            The agent's response as a string.

        Tool invocations made while handling this query are recorded and can
        be read with get_tool_trace(). The trace is cleared at the start of
        this call. query_with_trace() returns the answer and that trace together.
        """
        self._tool_calls.clear()

        logger.info(f"\n{'='*60}")
        logger.info(f"📨 New query received: {user_query[:100]}..." if len(
            user_query) > 100 else f"📨 New query received: {user_query}")

        if metadata:
            logger.debug(f"Query metadata: {metadata}")

        # Get conversation history from memory
        from llama_index.core.llms import ChatMessage, MessageRole
        conversation_history = self.memory.get()

        # Format the query with metadata and conversation history
        formatted_query = self._format_query_with_history(
            user_query, metadata, conversation_history)
        logger.debug("Query formatted with conversation history")

        # Create a new async function to run the agent
        async def run_agent_async():
            logger.info("🤔 Agent is thinking...")
            # The run method returns an EventResponse, we need to await it
            response = await self.agent.run(formatted_query)
            logger.info("✅ Agent has formulated a response")
            return response

        # Run the async function in a new event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a new thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, run_agent_async())
                    response = future.result()
            else:
                response = loop.run_until_complete(run_agent_async())
        except RuntimeError:
            # No event loop exists, create one
            response = asyncio.run(run_agent_async())

        response_str = str(response)

        # Store the conversation in memory
        self.memory.put(ChatMessage(role=MessageRole.USER, content=user_query))
        self.memory.put(ChatMessage(
            role=MessageRole.ASSISTANT, content=response_str))

        logger.info(f"💬 Response length: {len(response_str)} characters")
        logger.debug(f"Response preview: {response_str[:200]}..." if len(
            response_str) > 200 else f"Response: {response_str}")
        logger.info(f"{'='*60}\n")
        return response_str

    def query_with_trace(
        self,
        user_query: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a customer query and return the answer plus tool-call trace.

        The trace lists each tool the agent actually invoked, in call order.
        It is not inferred from the final answer.

        Args:
            user_query: The customer's question or request
            metadata: Optional metadata about the query (customer_id, etc.)

        Returns:
            A dict with:
            - answer: the same string query() returns
            - tool_calls: list of {order, name, arguments} in call order
        """
        answer = self.query(user_query, metadata)
        return {
            "answer": answer,
            "tool_calls": self.get_tool_trace(),
        }

    def _format_query(self, query: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Format the user query with any additional metadata.

        Args:
            query: Raw user query
            metadata: Optional metadata dict

        Returns:
            Formatted query string
        """
        if not metadata:
            return query

        # Add metadata context if provided
        context_parts = []
        if "customer_id" in metadata:
            context_parts.append(f"Customer ID: {metadata['customer_id']}")
        if "customer_email" in metadata:
            context_parts.append(
                f"Customer Email: {metadata['customer_email']}")
        if "account_type" in metadata:
            context_parts.append(f"Account Type: {metadata['account_type']}")

        if context_parts:
            context = " | ".join(context_parts)
            return f"[{context}]\n\n{query}"

        return query

    def _format_query_with_history(
        self,
        query: str,
        metadata: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List] = None
    ) -> str:
        """
        Format the user query with metadata and conversation history.

        Args:
            query: Raw user query
            metadata: Optional metadata dict
            conversation_history: List of ChatMessage objects from memory

        Returns:
            Formatted query string with conversation context
        """
        # Start with the base query
        formatted_parts = []

        # Add conversation history if available
        if conversation_history:
            history_text = "Previous conversation:\n"
            for msg in conversation_history:
                role = "User" if msg.role == "user" else "Assistant"
                history_text += f"{role}: {msg.content}\n"
            formatted_parts.append(history_text)

        # Add metadata context if provided
        if metadata:
            context_parts = []
            if "customer_id" in metadata:
                context_parts.append(f"Customer ID: {metadata['customer_id']}")
            if "customer_email" in metadata:
                context_parts.append(
                    f"Customer Email: {metadata['customer_email']}")
            if "account_type" in metadata:
                context_parts.append(
                    f"Account Type: {metadata['account_type']}")

            if context_parts:
                formatted_parts.append("[" + " | ".join(context_parts) + "]")

        # Add the current query
        formatted_parts.append(f"Current query: {query}")

        return "\n\n".join(formatted_parts)

    def reset_memory(self):
        """Reset the conversation memory."""
        self.memory.reset()

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get the conversation history.

        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        messages = []
        try:
            # Try to get messages from memory
            chat_history = self.memory.get_all()
            for msg in chat_history:
                messages.append({
                    "role": getattr(msg, 'role', 'unknown'),
                    "content": getattr(msg, 'content', str(msg))
                })
        except AttributeError:
            # If get_all doesn't exist, try other methods
            try:
                chat_history = self.memory.chat_history
                for msg in chat_history:
                    messages.append({
                        "role": getattr(msg, 'role', 'unknown'),
                        "content": getattr(msg, 'content', str(msg))
                    })
            except:
                # If all else fails, return empty list
                pass
        return messages
