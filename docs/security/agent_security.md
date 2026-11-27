# Agenten- und Modellberechtigungen, 27.11.2026

Dokumente, Rechercheantworten, AgentSpecs und Modellantworten sind untrusted.
Rechte stammen aus Serverkonfiguration und aktuellem Principal. Der bestehende
Factory-/Registry-/Engine-/Gatewaypfad bleibt die einzige Ausführungsarchitektur.

| Grenze | Durchsetzung / Datei | Konkrete Regression |
|---|---|---|
| Actor → Registry | `backend/app/agents/agent_registry.py`: process-Recht, servergebundener owner_subject, kein fremder Parent | `tests/security/test_secure_document_gateway.py::test_another_actor_cannot_delegate_from_a_registered_parent` |
| Vorschlag → Kindagent | `agents/agent_factory.py`, `adaptive_assessment.py`: Rolle, Kategorie, Kriterium, Belege, Parent, gleiches Run/Class-Scope, Modell-/Tool-/Dokumentteilmengen, Tiefe/Budgets | `tests/unit/test_semantic_planning.py`, `tests/security/test_agent_guardrails.py` |
| Engine → Dokumentoperation | `security/tool_permissions.py::authorize_tool_call`: registrierte Identität, Owner, read/process, feste Zwecke, Run/Dokument, Klassifizierungsgrenze, kein Netzwerkziel, keine freien Parameter, nur document.read | `tests/security/test_secure_document_gateway.py::test_tool_firewall_checks_every_grant_before_execution`, `test_tool_read_cannot_exceed_the_registered_agent_classification` |
| Agent → Modell | `core/execution_engine.py` bindet ContextVar; `llm/gateway.py` prüft Actor, festes Modell/Rolle und Labels/Scope; Reset im finally | `tests/security/test_injection_controls.py::test_model_dispatch_is_bound_to_the_current_agent_even_for_valid_local_models` |
| Dokument → Modell | Gateway benötigt read und process bei Dokumentlabel; bestehende Policy-/Egress-/Providerbindung bleibt obligatorisch | `test_document_inference_requires_read_permission_before_budget_or_dispatch`, bestehende externe Modell-/IFC-Tests |
| Nachrichten → Provider | exakte role/content-Felder, nur system/user/assistant und Stringinhalt; keine freien tool/function-Nachrichten | `security/tool_permissions.py::validate_model_messages`, bestehende Gateway-/Guardrailtests |
| Modellantwort → Befund | rohes JSON vor Schema-Konvertierung prüfen; verboten u.a. tool_calls/function_call, grade/points/score, shell_command/policy_override und selbsternannte SECURITY_INCIDENT; danach Schema-/Evidenz-/Coverageprüfung | `tests/security/test_injection_controls.py::test_lax_output_schema_cannot_silently_drop_a_tool_or_grade_request` |

Kein Modelloutput löst Shell, Dateizugriff, Konfigurationsänderung, externe
Modellauswahl oder Katalogmutation aus. Auch semantische Agentenvorschläge
benutzen feste serverseitige Mechanismen. Pflichtkriterien werden unabhängig vom
Output geprüft. Verbotene Strukturfelder sind keine vollständige semantische
Erkennung manipulierter Aussagen; erlaubte Befunde können dennoch fachlich falsch sein.

`ExecutionEngine.ask` passiert die Toolprüfung vor der festen Interaktion;
Modellcalls passieren zusätzlich das Gateway. Primärreviews und Quellenreviews
benutzen feste Anwendungspfade mit Objekt-ACL, nicht eine dynamische Toolliste.
Der Kontext ist eine interne Python-Vertrauensgrenze. Ein Angreifer mit beliebiger
Codeausführung im Backend könnte ihn verändern; dafür braucht es unabhängige
Prozess-/Hostkontrollen. Die Demoidentität ist keine Hochschul-SSO oder
produktive Mandantentrennung.

Die Recherche-Runtime bleibt geschlossen. Ein PUBLIC-Snapshot kann manipulative
Literatur enthalten; er erbt dadurch keine Rechte. PRIVATE/RESTRICTED bleibt für
reale Verarbeitung gesperrt. Menschliche Sicherheitsfreigabe erweitert weder
Modell-, Netzwerk-, Werkzeug- noch Dokumentberechtigungen.

Einheitlich positive Befunde in auffälligem Dokumentkontext erzwingen ergänzende
Gegenprüfung und menschliche Klärung. Die Regression bewahrt die positiven
Urteile und ändert keine Note. Reale Unabhängigkeit und fachliche Qualität der
Modelle sind mangels freigegebener Artefakte nicht empirisch belegt.
