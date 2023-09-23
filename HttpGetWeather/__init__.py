import logging
import weather
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    # Begin HTTP Function
    logging.info('Python HTTP trigger function processed a request.')

    location = req.params.get('loc')
    if not location:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            loc = req_body.get('loc')

    if loc:
        if weather.get_loc_code(loc) == 'None':
            return func.HttpResponse(f"Location '{loc}' does not exist or is not currently supported")
        else:
            weather.process_weather(loc)
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
