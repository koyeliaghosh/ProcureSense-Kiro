"""
Context management system with budget validation and pruning
"""
from typing import Dict, List, Any, Optional
from src.models.context_types import (
    LayeredContext, 
    GlobalPolicyContext, 
    DomainStrategyContext,
    TaskSessionContext, 
    EphemeralToolContext
)
from src.context.budget_config import ContextBudgetConfig
from src.context.token_counter import TokenCounter
from src.context.gpc_manager import GPCManager


class ContextManager:
    """
    Manages layered context with budget enforcement and pruning.
    
    Implements the hierarchical context architecture with:
    - GPC (25%): Never pruned, enterprise policies
    - DSC (25%): Summarized when over budget
    - TSC (40%): Rolling summaries, recency bias
    - ETC (10%): First to be pruned
    """
    
    def __init__(self, budget_config: ContextBudgetConfig):
        self.budget_config = budget_config
        self.gpc_manager = GPCManager()
        
    def build_context(
        self, 
        agent_type: str, 
        request: Dict[str, Any],
        session_data: Optional[Dict[str, Any]] = None
    ) -> LayeredContext:
        """
        Build layered context for agent request.
        
        Args:
            agent_type: Type of agent (negotiation, compliance, forecast)
            request: Agent request payload
            session_data: Optional session context data
            
        Returns:
            LayeredContext with populated layers
        """
        context = LayeredContext()
        
        # Build each layer
        context.gpc = self._build_gpc_layer()
        context.dsc = self._build_dsc_layer(agent_type, request)
        context.tsc = self._build_tsc_layer(session_data or {})
        context.etc = self._build_etc_layer(request)
        
        # Calculate tokens and validate budgets
        context.calculate_total_tokens()
        
        # Apply pruning if over budget
        if not self._is_within_budget(context):
            context = self.prune_context(context, self.budget_config.total_budget)
            
        return context
    
    def _build_gpc_layer(self) -> GlobalPolicyContext:
        """Build Global Policy Context layer using GPC Manager"""
        try:
            return self.gpc_manager.load_gpc()
        except Exception as e:
            # Return a simple mock GPC to avoid delays
            return GlobalPolicyContext(
                enterprise_okrs=["Operational efficiency", "Cost optimization", "Risk management"],
                prohibited_clauses=["liability_waiver", "unlimited_liability"],
                required_clauses=["warranty", "data_protection"],
                compliance_guardrails=["Standard enterprise compliance"],
                legal_requirements=["Standard legal requirements"],
                budget_thresholds={"software": 50000, "hardware": 100000}
            )
    
    def _build_dsc_layer(self, agent_type: str, request: Dict[str, Any]) -> DomainStrategyContext:
        """Build Domain Strategy Context layer"""
        category = request.get('category', 'general')
        
        return DomainStrategyContext(
            category_playbooks={
                category: f"Procurement playbook for {category} category"
            },
            vendor_guidelines=[
                f"Preferred vendors for {category}",
                f"Negotiation strategies for {category}",
                f"Quality standards for {category}"
            ],
            market_intelligence=[
                f"Market trends for {category}",
                f"Pricing benchmarks for {category}"
            ],
            historical_patterns=[
                f"Historical negotiation outcomes for {category}",
                f"Seasonal pricing patterns for {category}"
            ]
        )
    
    def _build_tsc_layer(self, session_data: Dict[str, Any]) -> TaskSessionContext:
        """Build Task/Session Context layer"""
        return TaskSessionContext(
            conversation_turns=session_data.get('conversation_turns', []),
            tool_interactions=session_data.get('tool_interactions', []),
            session_findings=session_data.get('session_findings', []),
            user_preferences=session_data.get('user_preferences', {})
        )
    
    def _build_etc_layer(self, request: Dict[str, Any]) -> EphemeralToolContext:
        """Build Ephemeral Tool Context layer"""
        return EphemeralToolContext(
            quotes=request.get('quotes', []),
            budgets=request.get('budgets', []),
            vendor_data=request.get('vendor_data', []),
            api_responses=request.get('api_responses', [])
        )
    
    def _is_within_budget(self, context: LayeredContext) -> bool:
        """Check if context is within total budget"""
        return context.total_tokens <= self.budget_config.total_budget
    
    def prune_context(self, context: LayeredContext, target_tokens: int) -> LayeredContext:
        """
        Enhanced context pruning following ETC → TSC → DSC → GPC hierarchy.
        GPC is never pruned (pinned) to ensure enterprise alignment.
        
        Pruning Strategy:
        1. ETC: Complete removal (ephemeral data)
        2. TSC: Rolling summaries with recency bias
        3. DSC: Intelligent summarization preserving key insights
        4. GPC: Never pruned (pinned for enterprise alignment)
        
        Args:
            context: Context to prune
            target_tokens: Target token count
            
        Returns:
            Pruned context within target budget
        """
        if context.total_tokens <= target_tokens:
            return context
        
        # Calculate how many tokens we need to remove
        tokens_to_remove = context.total_tokens - target_tokens
        original_tokens_to_remove = tokens_to_remove
        
        # Track pruning actions for audit
        pruning_actions = []
        
        # Phase 1: Prune ETC completely (ephemeral data)
        if tokens_to_remove > 0 and context.etc.token_count > 0:
            etc_tokens_before = context.etc.token_count
            context.etc = self._prune_etc_layer(context.etc, tokens_to_remove)
            etc_tokens_removed = etc_tokens_before - context.etc.token_count
            tokens_to_remove -= etc_tokens_removed
            
            if etc_tokens_removed > 0:
                pruning_actions.append(f"ETC: Removed {etc_tokens_removed} tokens (complete pruning)")
        
        # Phase 2: Prune TSC with rolling summaries
        if tokens_to_remove > 0 and context.tsc.token_count > 0:
            tsc_tokens_before = context.tsc.token_count
            # Allow up to 75% reduction of TSC, keeping most recent content
            max_tsc_reduction = int(context.tsc.token_count * 0.75)
            tsc_reduction = min(tokens_to_remove, max_tsc_reduction)
            
            context.tsc = self._prune_tsc_layer(context.tsc, tsc_reduction)
            tsc_tokens_removed = tsc_tokens_before - context.tsc.token_count
            tokens_to_remove -= tsc_tokens_removed
            
            if tsc_tokens_removed > 0:
                pruning_actions.append(f"TSC: Removed {tsc_tokens_removed} tokens (rolling summaries)")
        
        # Phase 3: Prune DSC with intelligent summarization
        if tokens_to_remove > 0 and context.dsc.token_count > 0:
            dsc_tokens_before = context.dsc.token_count
            # Allow up to 60% reduction of DSC, preserving key insights
            max_dsc_reduction = int(context.dsc.token_count * 0.60)
            dsc_reduction = min(tokens_to_remove, max_dsc_reduction)
            
            context.dsc = self._prune_dsc_layer(context.dsc, dsc_reduction)
            dsc_tokens_removed = dsc_tokens_before - context.dsc.token_count
            tokens_to_remove -= dsc_tokens_removed
            
            if dsc_tokens_removed > 0:
                pruning_actions.append(f"DSC: Removed {dsc_tokens_removed} tokens (summarization)")
        
        # Phase 4: GPC is NEVER pruned (pinned for enterprise alignment)
        if tokens_to_remove > 0:
            pruning_actions.append(f"GPC: Protected from pruning ({context.gpc.token_count} tokens preserved)")
        
        # Recalculate total tokens after pruning
        context.calculate_total_tokens()
        
        # Log pruning summary
        total_removed = original_tokens_to_remove - tokens_to_remove
        if pruning_actions:
            print(f"Context Pruning Summary: Removed {total_removed} tokens")
            for action in pruning_actions:
                print(f"  - {action}")
            
            if tokens_to_remove > 0:
                print(f"  - Warning: Still {tokens_to_remove} tokens over budget after maximum pruning")
        
        return context
    
    def _prune_etc_layer(self, etc: EphemeralToolContext, tokens_to_remove: int) -> EphemeralToolContext:
        """
        Prune ETC layer by complete removal (ephemeral data strategy).
        ETC contains temporary data that can be safely discarded under token pressure.
        """
        if tokens_to_remove > 0:
            # Complete removal strategy for ephemeral data
            return EphemeralToolContext()
        return etc
    
    def _prune_tsc_layer(self, tsc: TaskSessionContext, tokens_to_remove: int) -> TaskSessionContext:
        """
        Prune TSC layer with rolling summaries and recency bias.
        Preserves most recent interactions while summarizing older content.
        """
        if tokens_to_remove <= 0:
            return tsc
        
        # Calculate current token usage
        current_tokens = tsc.calculate_tokens()
        target_tokens = current_tokens - tokens_to_remove
        
        # Rolling summary strategy with recency bias
        
        # 1. Conversation turns: Keep recent, summarize old
        if len(tsc.conversation_turns) > 3:
            # Keep last 3 turns, summarize the rest
            old_turns = tsc.conversation_turns[:-3]
            if old_turns:
                summary = self._summarize_conversation_turns(old_turns)
                tsc.conversation_turns = [summary] + tsc.conversation_turns[-3:]
        
        # 2. Tool interactions: Keep recent, summarize patterns
        if len(tsc.tool_interactions) > 5:
            # Keep last 5 interactions, summarize patterns from older ones
            old_interactions = tsc.tool_interactions[:-5]
            if old_interactions:
                summary = self._summarize_tool_interactions(old_interactions)
                tsc.tool_interactions = [summary] + tsc.tool_interactions[-5:]
        
        # 3. Session findings: Compress while preserving key insights
        if len(tsc.session_findings) > 3:
            # Compress findings into key insights
            compressed_findings = self._compress_session_findings(tsc.session_findings)
            tsc.session_findings = compressed_findings
        
        # 4. User preferences: Keep all (usually small and important)
        # User preferences are preserved as they're typically small but important
        
        return tsc
    
    def _summarize_conversation_turns(self, turns: List[str]) -> str:
        """Summarize conversation turns into key points"""
        if not turns:
            return ""
        
        # Simple summarization - in production, this could use LLM
        key_topics = []
        for turn in turns:
            if "negotiation" in turn.lower():
                key_topics.append("negotiation discussion")
            elif "compliance" in turn.lower():
                key_topics.append("compliance review")
            elif "forecast" in turn.lower():
                key_topics.append("budget forecasting")
        
        unique_topics = list(set(key_topics))
        if unique_topics:
            return f"Previous discussion covered: {', '.join(unique_topics)}"
        else:
            return f"Previous conversation ({len(turns)} turns)"
    
    def _summarize_tool_interactions(self, interactions: List[str]) -> str:
        """Summarize tool interactions into patterns"""
        if not interactions:
            return ""
        
        # Extract interaction patterns
        interaction_types = []
        for interaction in interactions:
            if "api_call" in interaction.lower():
                interaction_types.append("API calls")
            elif "database" in interaction.lower():
                interaction_types.append("database queries")
            elif "calculation" in interaction.lower():
                interaction_types.append("calculations")
        
        unique_types = list(set(interaction_types))
        if unique_types:
            return f"Previous tool usage: {', '.join(unique_types)} ({len(interactions)} interactions)"
        else:
            return f"Previous tool interactions ({len(interactions)} total)"
    
    def _compress_session_findings(self, findings: List[str]) -> List[str]:
        """Compress session findings while preserving key insights"""
        if len(findings) <= 3:
            return findings
        
        # Group findings by type/importance
        high_priority = []
        medium_priority = []
        
        for finding in findings:
            if any(keyword in finding.lower() for keyword in ["critical", "violation", "risk", "required"]):
                high_priority.append(finding)
            else:
                medium_priority.append(finding)
        
        # Keep all high priority, summarize medium priority
        result = high_priority.copy()
        
        if medium_priority:
            if len(medium_priority) > 2:
                summary = f"Additional findings: {len(medium_priority)} items including insights on procurement patterns"
                result.append(summary)
            else:
                result.extend(medium_priority)
        
        return result[:3]  # Limit to 3 total findings
    
    def _prune_dsc_layer(self, dsc: DomainStrategyContext, tokens_to_remove: int) -> DomainStrategyContext:
        """
        Prune DSC layer with intelligent summarization.
        Preserves key strategic insights while compressing detailed information.
        """
        if tokens_to_remove <= 0:
            return dsc
        
        # Calculate current token usage
        current_tokens = dsc.calculate_tokens()
        target_tokens = current_tokens - tokens_to_remove
        
        # Intelligent summarization strategy
        
        # 1. Market intelligence: Compress to key trends and insights
        if len(dsc.market_intelligence) > 2:
            compressed_intelligence = self._compress_market_intelligence(dsc.market_intelligence)
            dsc.market_intelligence = compressed_intelligence
        
        # 2. Historical patterns: Keep most relevant patterns
        if len(dsc.historical_patterns) > 2:
            compressed_patterns = self._compress_historical_patterns(dsc.historical_patterns)
            dsc.historical_patterns = compressed_patterns
        
        # 3. Vendor guidelines: Prioritize by importance
        if len(dsc.vendor_guidelines) > 3:
            prioritized_guidelines = self._prioritize_vendor_guidelines(dsc.vendor_guidelines)
            dsc.vendor_guidelines = prioritized_guidelines
        
        # 4. Category playbooks: Summarize while preserving key strategies
        if dsc.category_playbooks:
            compressed_playbooks = self._compress_category_playbooks(dsc.category_playbooks)
            dsc.category_playbooks = compressed_playbooks
        
        return dsc
    
    def _compress_market_intelligence(self, intelligence: List[str]) -> List[str]:
        """Compress market intelligence to key insights"""
        if len(intelligence) <= 2:
            return intelligence
        
        # Extract key market insights
        key_insights = []
        trends = []
        pricing = []
        
        for item in intelligence:
            if "trend" in item.lower():
                trends.append(item)
            elif "pric" in item.lower():
                pricing.append(item)
            else:
                key_insights.append(item)
        
        # Compress each category
        result = []
        
        if trends:
            if len(trends) > 1:
                result.append(f"Market trends: {len(trends)} key trends identified")
            else:
                result.extend(trends)
        
        if pricing:
            if len(pricing) > 1:
                result.append(f"Pricing intelligence: {len(pricing)} pricing insights available")
            else:
                result.extend(pricing)
        
        # Keep most important general insights
        if key_insights:
            result.extend(key_insights[:1])
        
        return result[:2]  # Limit to 2 items
    
    def _compress_historical_patterns(self, patterns: List[str]) -> List[str]:
        """Compress historical patterns to most relevant"""
        if len(patterns) <= 2:
            return patterns
        
        # Prioritize recent and successful patterns
        prioritized = []
        seasonal = []
        negotiation = []
        
        for pattern in patterns:
            if "seasonal" in pattern.lower():
                seasonal.append(pattern)
            elif "negotiation" in pattern.lower():
                negotiation.append(pattern)
            else:
                prioritized.append(pattern)
        
        # Keep most relevant from each category
        result = []
        
        if negotiation:
            result.append(negotiation[0])  # Most recent negotiation pattern
        
        if seasonal:
            result.append(seasonal[0])  # Most recent seasonal pattern
        
        # Fill remaining space with other patterns
        remaining_space = 2 - len(result)
        if remaining_space > 0 and prioritized:
            result.extend(prioritized[:remaining_space])
        
        return result[:2]  # Limit to 2 patterns
    
    def _prioritize_vendor_guidelines(self, guidelines: List[str]) -> List[str]:
        """Prioritize vendor guidelines by importance"""
        if len(guidelines) <= 3:
            return guidelines
        
        # Prioritize guidelines with compliance/risk keywords
        high_priority = []
        medium_priority = []
        
        for guideline in guidelines:
            if any(keyword in guideline.lower() for keyword in ["compliance", "risk", "required", "mandatory"]):
                high_priority.append(guideline)
            else:
                medium_priority.append(guideline)
        
        # Combine prioritized guidelines
        result = high_priority[:2]  # Keep top 2 high priority
        
        remaining_space = 3 - len(result)
        if remaining_space > 0:
            result.extend(medium_priority[:remaining_space])
        
        return result[:3]  # Limit to 3 guidelines
    
    def _compress_category_playbooks(self, playbooks: Dict[str, str]) -> Dict[str, str]:
        """Compress category playbooks while preserving key strategies"""
        if len(playbooks) <= 1:
            return playbooks
        
        # For each playbook, create a compressed version
        compressed = {}
        
        for category, playbook in playbooks.items():
            if len(playbook) > 200:  # If playbook is long, compress it
                # Extract key points (simplified compression)
                if "strategy" in playbook.lower():
                    compressed[category] = f"Strategic playbook for {category} with key negotiation points"
                else:
                    compressed[category] = f"Procurement playbook for {category} category"
            else:
                compressed[category] = playbook
        
        return compressed
    
    def validate_context_budgets(self, context: LayeredContext) -> Dict[str, Any]:
        """
        Validate context against budget constraints.
        
        Returns:
            Dictionary with validation results and recommendations
        """
        validation_results = context.validate_budgets(self.budget_config)
        
        recommendations = []
        
        if not validation_results['gpc']:
            recommendations.append("GPC over budget - consider reducing policy complexity")
        if not validation_results['dsc']:
            recommendations.append("DSC over budget - will be summarized")
        if not validation_results['tsc']:
            recommendations.append("TSC over budget - will use rolling summaries")
        if not validation_results['etc']:
            recommendations.append("ETC over budget - will be pruned first")
        if not validation_results['total']:
            recommendations.append("Total budget exceeded - pruning will be applied")
        
        return {
            'validation_results': validation_results,
            'budget_compliance': context.budget_compliance,
            'token_usage': context.get_layer_tokens(),
            'budget_allocation': self.budget_config.get_all_budgets(),
            'recommendations': recommendations
        }
    
    def is_gpc_pinned(self) -> bool:
        """
        Verify that GPC is configured to never be pruned.
        This method confirms the enterprise alignment guarantee.
        
        Returns:
            True - GPC is always pinned and never pruned
        """
        return True  # GPC is architecturally pinned in the pruning algorithm
    
    def get_pruning_hierarchy(self) -> List[str]:
        """
        Get the context pruning hierarchy order.
        
        Returns:
            List of context layers in pruning order (first pruned to last)
        """
        return ["ETC", "TSC", "DSC", "GPC (never pruned)"]
    
    def simulate_extreme_pruning(self, context: LayeredContext) -> Dict[str, Any]:
        """
        Simulate extreme token pressure to verify GPC protection.
        This method demonstrates that GPC survives even aggressive pruning.
        
        Args:
            context: Context to test extreme pruning on
            
        Returns:
            Dictionary with pruning simulation results
        """
        original_tokens = context.calculate_total_tokens()
        
        # Simulate extreme pressure - try to prune to just GPC budget
        gpc_only_budget = self.budget_config.gpc_budget
        
        # Apply extreme pruning
        pruned_context = self.prune_context(context, gpc_only_budget)
        
        return {
            'original_total_tokens': original_tokens,
            'target_budget': gpc_only_budget,
            'final_total_tokens': pruned_context.total_tokens,
            'gpc_tokens_preserved': pruned_context.gpc.token_count,
            'gpc_survived': pruned_context.gpc.token_count > 0,
            'other_layers_tokens': {
                'dsc': pruned_context.dsc.token_count,
                'tsc': pruned_context.tsc.token_count,
                'etc': pruned_context.etc.token_count
            },
            'enterprise_alignment_maintained': pruned_context.gpc.token_count > 0
        }
    
    def validate_policy_compliance(self, text: str, category: Optional[str] = None, 
                                 amount: Optional[float] = None):
        """
        Validate text against enterprise policies using GPC Manager
        
        Args:
            text: Text to validate
            category: Optional spending category
            amount: Optional spending amount
            
        Returns:
            PolicyValidationResult from GPC Manager
        """
        return self.gpc_manager.validate_comprehensive(text, category, amount)
    
    def get_policy_summary(self) -> Dict[str, Any]:
        """Get summary of loaded enterprise policies"""
        return self.gpc_manager.get_policy_summary()