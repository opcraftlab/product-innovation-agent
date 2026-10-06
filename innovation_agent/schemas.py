"""Portable schemas; all model output fields are explicit and required."""
import math

DIMENSIONS = ("fit", "demand", "difference", "experience", "feasibility", "economics", "communication", "channel")
KINDS = ("desk", "interview", "observation", "preference", "behavior", "technical", "quote", "capability", "transaction", "retention", "delivery", "simulation")
STAGES = ("explore", "prototype", "pilot", "scale")

def text(): return {"type": "string", "minLength": 1}
def enum(*items): return {"type": "string", "enum": list(items)}
def array(item, minimum=0, maximum=100): return {"type": "array", "items": item, "minItems": minimum, "maxItems": maximum}
def obj(**props): return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}
def number(minimum=0): return {"type": "number", "minimum": minimum}
def integer(minimum=0, maximum=1000000): return {"type": "integer", "minimum": minimum, "maximum": maximum}

BRIEF_SCHEMA = obj(
    title=text(), decision=text(), target_user=text(), payer=text(), market=text(),
    current_alternative=text(), business_goal=text(), assets=array(text()),
    target_stage=enum(*STAGES), max_directions=integer(1,8),
    budget=number(), currency=text(), deadline=text(),
    constraints=array(obj(id=text(), description=text(), status=enum("unknown","pass","fail"), candidate_ids=array(text(),1))),
    synthetic={"type":"boolean"},
)
EVIDENCE_ITEM = obj(
    id=text(), statement=text(), kind=enum(*KINDS), source=text(), date=text(),
    sample_size=integer(), verified={"type":"boolean"}, synthetic={"type":"boolean"},
    dimensions=array(enum(*DIMENSIONS),1,8), candidate_ids=array(text(),1), limitations=text(),
)
EVIDENCE_SCHEMA = array(EVIDENCE_ITEM,0,500)
ASSESSMENT = obj(status=enum("unknown","promising","supported","contradicted"), reason=text(),
                 evidence_ids=array(text()), counter_evidence_ids=array(text()))
CANDIDATE = obj(
    id=text(), title=text(), segment=text(), scenario=text(), current_alternative=text(),
    problem=text(), desired_progress=text(), value_proposition=text(),
    innovation_lever=enum("segment","scenario","experience","technology","understanding","combination"),
    market_route=enum("new_solution","better_standard","focused_segment","unclear"),
    product_definition=text(), experience_design=text(), delivery_path=text(),
    communication=text(), purchase_journey=text(), economics_hypothesis=text(),
    defensibility=text(), capability_gaps=array(text()), assumptions=array(text(),1),
    assessments=obj(**{d:ASSESSMENT for d in DIMENSIONS}),
)
EXPERIMENT = obj(
    id=text(), candidate_id=text(), dimension=enum(*DIMENSIONS), hypothesis=text(),
    method=text(), comparison=text(), metric=text(), pass_rule=text(), stop_rule=text(),
    sample_plan=text(), max_cost=number(), days=integer(1,365), owner=text(),
)
ANALYSIS_SCHEMA = obj(
    input_digest=text(), task_summary=text(), opportunity_logic=text(),
    market_maturity=text(), missing_information=array(text()),
    candidates=array(CANDIDATE,1,8), experiments=array(EXPERIMENT,1,24),
    portfolio_recommendation=text(), next_actions=array(text(),1,12),
)

class ValidationError(ValueError): pass

def validate(value, schema, path="$ "):
    """Validate the small documented JSON Schema subset used in this project."""
    kind=schema["type"]
    if kind=="object":
        if not isinstance(value,dict): raise ValidationError(f"{path}: expected object")
        missing=set(schema["required"])-set(value)
        extra=set(value)-set(schema["properties"])
        if missing or extra: raise ValidationError(f"{path}: missing={sorted(missing)}, extra={sorted(extra)}")
        for key,sub in schema["properties"].items():
            if key in value: validate(value[key],sub,f"{path}.{key}")
    elif kind=="array":
        if not isinstance(value,list): raise ValidationError(f"{path}: expected array")
        if not schema.get("minItems",0)<=len(value)<=schema.get("maxItems",1000000):
            raise ValidationError(f"{path}: invalid item count")
        for i,v in enumerate(value): validate(v,schema["items"],f"{path}[{i}]")
    elif kind=="string":
        if not isinstance(value,str) or len(value.strip())<schema.get("minLength",0):
            raise ValidationError(f"{path}: expected non-empty string")
        if "enum" in schema and value not in schema["enum"]: raise ValidationError(f"{path}: invalid choice {value!r}")
    elif kind=="boolean":
        if type(value) is not bool: raise ValidationError(f"{path}: expected boolean")
    elif kind in ("integer","number"):
        if type(value) not in (int,float) or not math.isfinite(value): raise ValidationError(f"{path}: expected finite number")
        if kind=="integer" and type(value) is not int: raise ValidationError(f"{path}: expected integer")
        if value<schema.get("minimum",-math.inf) or value>schema.get("maximum",math.inf): raise ValidationError(f"{path}: out of range")
    else: raise ValidationError(f"Unsupported schema type: {kind}")
