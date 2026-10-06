"""One explicit Responses API call. No hidden retries or autonomous spending."""
import json
import urllib.error
import urllib.request
from .schemas import ANALYSIS_SCHEMA, ValidationError

ENDPOINT="https://api.openai.com/v1/responses"

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

def parse_response(data):
    if data.get("status")!="completed":
        raise ValidationError("Model response was not completed; no analysis was saved")
    texts=[]
    for item in data.get("output",[]):
        if item.get("type")!="message": continue
        for part in item.get("content",[]):
            if part.get("type")=="refusal": raise ValidationError("Model refused this request; no analysis was saved")
            if part.get("type")=="output_text": texts.append(part.get("text",""))
    if not texts: raise ValidationError("Model returned no text")
    try: result=json.loads("".join(texts))
    except json.JSONDecodeError: raise ValidationError("Model output is not valid JSON; no analysis was saved")
    return result

def generate(system,user,model,key,max_output_tokens=10000,timeout=120,opener=None,*,schema=None):
    if not key or not model: raise ValidationError("Set OPENAI_API_KEY and INNOVATION_MODEL before running API mode")
    if not 1000<=max_output_tokens<=32000: raise ValidationError("max_output_tokens must be 1000..32000")
    if not 1<=timeout<=600: raise ValidationError("timeout must be 1..600 seconds")
    payload={"model":model,"instructions":system,"input":user,"store":False,
             "max_output_tokens":max_output_tokens,
             "text":{"format":{"type":"json_schema","name":"innovation_analysis","strict":True,"schema":api_schema(schema if schema is not None else ANALYSIS_SCHEMA)}}}
    req=urllib.request.Request(ENDPOINT,data=json.dumps(payload).encode(),method="POST",
          headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
    client=opener or urllib.request.build_opener(NoRedirect())
    try:
        with client.open(req,timeout=timeout) as response:
            raw=response.read(4_000_001)
        if len(raw)>4_000_000: raise ValidationError("API response exceeds limit")
        data=json.loads(raw)
    except urllib.error.HTTPError as exc:
        # Never echo provider response bodies: they may contain submitted project data.
        raise ValidationError(f"API HTTP {exc.code}; check model access, quota and request compatibility. No automatic retry.") from None
    except (urllib.error.URLError,TimeoutError): raise ValidationError("API network error/timeout. No automatic retry; check usage before retrying.") from None
    result=parse_response(data)
    return result,{"model":model,"response_id":data.get("id"),"usage":data.get("usage",{}),"live_api":True}

def api_schema(schema):
    """Keep length/range validation local; send a conservative strict API subset."""
    if isinstance(schema,list): return [api_schema(x) for x in schema]
    if not isinstance(schema,dict): return schema
    return {k:api_schema(v) for k,v in schema.items()
            if k not in {"minLength","maxLength","minimum","maximum","minItems","maxItems"}}
