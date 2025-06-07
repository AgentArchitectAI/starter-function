import json

def main(context):
    req = context.req
    res = context.res

    try:

        data = req.body
        context.log(f"[DEBUG] req.body (tipo {type(data)}): {data}")

        if not isinstance(data, dict) or "prompt" not in data:
            raise ValueError("El campo 'prompt' es requerido en el JSON.")

        prompt = data["prompt"]
        context.log(f"[DEBUG] Prompt final: {prompt}")

        return res.json({
            "ok": True,
            "prompt": prompt
        })

    except Exception as e:
        context.error(f"[ERROR]: {str(e)}")
        return res.json({ "error": str(e) }, 500)
