import { useState, useRef, useCallback, useEffect } from "react";

const API_KEY = "ff239b9b04b514b8bc57f166f0eebd8a6a67022575f7886c027b27728e53e6fd";

function generateId() {
  return crypto.randomUUID ? crypto.randomUUID() :
    'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
      const r = Math.random() * 16 | 0;
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
}

export function useLifecycle() {
  const [proposalId, setProposalId] = useState(generateId());
  const sessionId = useRef(generateId()).current;
  const [lifecycleState, setLifecycleStateRaw] = useState(null);
  const [researchMessageId, setResearchMessageId] = useState(null);
  const [reviewerMessageId, setReviewerMessageId] = useState(null);
  const [directiveHash, setDirectiveHash] = useState(null);
  const [directiveText, setDirectiveText] = useState(null);
  const [drafterResponseText, setDrafterResponseText] = useState(null);
  const [ericApproved, setEricApproved] = useState(false);
  const [ericBypass, setEricBypass] = useState(false);
  const [revisionCount, setRevisionCount] = useState(0);
  const [dispatchLog, setDispatchLog] = useState([]);
  const [verdict, setVerdict] = useState(null);
  const [critique, setCritique] = useState(null);
  const [requiredChanges, setRequiredChanges] = useState(null);
  const [lastError, setLastError] = useState(null);
  const [inFlight, setInFlight] = useState(false);
  const abortRef = useRef(null);
  const prevStateRef = useRef(null);

  const setLifecycleState = useCallback((val) => {
    if (val && val !== 'ERROR' && val !== 'ABORTED') {
      prevStateRef.current = val;
    }
    setLifecycleStateRaw(val);
    if (val === 'IDLE') {
      // Auto-reset
      setProposalId(generateId());
      setReviewerMessageId(null);
      setDirectiveHash(null);
      setDirectiveText(null);
      setDrafterResponseText(null);
      setResearchMessageId(null);
      setVerdict(null);
      setCritique(null);
      setRequiredChanges(null);
      setLastError(null);
      setDispatchLog([]);
      setEricApproved(false);
      setEricBypass(false);
      setRevisionCount(0);
    }
  }, []);

  const setError = useCallback((errorObj) => {
    setLastError({
      error: errorObj.error || "Unknown error",
      http_status_code: errorObj.http_status_code || 0,
      dispatch_id: errorObj.dispatch_id ?? null,
      action: errorObj.action ?? null,
      lifecycle_state: errorObj.lifecycle_state || 'ERROR',
    });
    setLifecycleStateRaw('ERROR');
    setInFlight(false);
  }, []);

  const clearError = useCallback(() => {
    setLastError(null);
    const prev = prevStateRef.current;
    setLifecycleStateRaw(prev || 'IDLE');
  }, []);

  const abort = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setInFlight(false);
    if (lifecycleState === 'EXECUTING') {
      setLifecycleStateRaw('UNVERIFIED');
    } else {
      setLifecycleStateRaw('ABORTED');
    }
  }, [lifecycleState]);

  const processResponse = useCallback((data) => {
    // 1. lifecycleState
    if (data.lifecycle_state != null) {
      setLifecycleState(data.lifecycle_state);
    }

    // 2. proposalId
    if (data.proposal_id && !proposalId) {
      setProposalId(data.proposal_id);
    }

    // 3. researchMessageId
    if (data.research_message_id != null) {
      setResearchMessageId(data.research_message_id);
    }

    // 4. reviewerMessageId
    if (data.reviewer_message_id != null) {
      setReviewerMessageId(data.reviewer_message_id);
    }

    // 5. directiveHash
    if (data.directive_hash != null) {
      setDirectiveHash(data.directive_hash);
    }

    // 6. directiveText
    if (data.directive_text != null) {
      setDirectiveText(data.directive_text);
    }

    // 7. ericApproved
    if (data.eric_approved != null) {
      setEricApproved(data.eric_approved === 1 || data.eric_approved === true);
    }

    // 8. ericBypass
    if (data.eric_bypass != null) {
      setEricBypass(data.eric_bypass === 1 || data.eric_bypass === true);
    }

    // 9. revisionCount
    if (data.revision_count != null) {
      setRevisionCount(data.revision_count);
    }

    // 10. verdict
    if (data.verdict != null) {
      setVerdict(data.verdict);
    }

    // 11. critique
    if (data.critique != null) {
      setCritique(data.critique);
    }

    // 12. requiredChanges
    if (data.required_changes != null) {
      setRequiredChanges(data.required_changes);
    }

    // 13. drafterResponseText
    if (data.lifecycle_state === 'DRAFT_READY' && data.content != null) {
      setDrafterResponseText(data.content);
    }
    if (data.agent_response && data.agent_response.content != null &&
        data.lifecycle_state === 'DRAFT_READY') {
      setDrafterResponseText(data.agent_response.content);
    }

    // 14. dispatchLog
    if (data.dispatch_id) {
      setDispatchLog(prev => [...prev, {
        dispatch_id: data.dispatch_id,
        source_actor: data.source_actor ?? null,
        target_agent: data.target_agent ?? null,
        target_endpoint: data.target_endpoint ?? null,
        current_status: data.lifecycle_state ?? 'UNKNOWN',
        timestamp_initiated: new Date().toISOString(),
        response_message_id: data.response_message_id ?? null,
        error_message: null,
      }]);
    }

    // 15. error
    if (data.status === 'ERROR' || data.status === 'STATE_CONFLICT') {
      setError(data);
    }

    // 16. inFlight
    setInFlight(false);
  }, [proposalId, setError, setLifecycleState]);

  const postAction = useCallback(async (action, extra = {}) => {
    setLastError(null);
    const controller = new AbortController();
    abortRef.current = controller;
    setInFlight(true);

    const body = {
      action,
      proposal_id: proposalId,
      session_id: sessionId,
      source_actor: 'eric',
      eric_approved: 1,
      ...extra,
    };

    try {
      const res = await fetch("/api/advisor/route", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CIS-API-Key": API_KEY,
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      const data = await res.json();
      processResponse(data);
    } catch (e) {
      if (e.name === 'AbortError') {
        if (lifecycleState === 'EXECUTING') {
          setLifecycleStateRaw('UNVERIFIED');
        } else {
          setLifecycleStateRaw('ABORTED');
        }
        setInFlight(false);
        abortRef.current = null;
      } else {
        setError({
          error: e.message,
          http_status_code: 0,
          dispatch_id: null,
          action: action,
          lifecycle_state: 'ERROR',
        });
      }
    }
    abortRef.current = null;
  }, [proposalId, sessionId, lifecycleState, processResponse, setError]);

  const resetProposal = useCallback(() => {
    setLifecycleState('IDLE');
  }, [setLifecycleState]);

  return {
    proposalId,
    sessionId,
    lifecycleState,
    researchMessageId,
    reviewerMessageId,
    directiveHash,
    directiveText,
    drafterResponseText,
    ericApproved,
    ericBypass,
    revisionCount,
    dispatchLog,
    verdict,
    critique,
    requiredChanges,
    lastError,
    inFlight,
    postAction,
    processResponse,
    setError,
    clearError,
    abort,
    resetProposal,
  };
}
