from flask import Flask, request, redirect
from random import randint
import logging

from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.trace import Status, StatusCode

# Define resource attributes
resource = Resource(attributes={
    "service.name": "rolldice",
    "service.namespace": "demo"
})

# Set up tracing
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer_provider = trace.get_tracer_provider()
tracer_provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint="http://k8s-infra-otel-agent.platform.svc.cluster.local:4318/v1/traces"
        )
    )
)
tracer = trace.get_tracer("diceroller.tracer")

# Set up metrics
metric_exporter = OTLPMetricExporter(
    endpoint="http://k8s-infra-otel-agent.platform.svc.cluster.local:4318/v1/metrics"
)
reader = PeriodicExportingMetricReader(metric_exporter)
metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))
meter = metrics.get_meter("diceroller.meter")

roll_counter = meter.create_counter(
    name="dice.rolls",
    description="The number of rolls by roll value"
)

# Initialize Flask app
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/")
def index():
    return redirect("/rolldice")

@app.route("/rolldice")
def roll_dice():
    with tracer.start_as_current_span("roll") as roll_span:
        player = request.args.get('player', default="anonymous", type=str)
        try:
            result = roll()
            roll_span.set_attribute("roll.value", result)
            roll_counter.add(1, {"roll.value": str(result)})

            logger.warning("%s is rolling the dice: %s", player, result)
            return str(result)

        except Exception as e:
            roll_span.record_exception(e)
            roll_span.set_status(Status(StatusCode.ERROR, str(e)))
            logger.error("Exception while rolling: %s", e)
            return f"Error: {str(e)}", 500

def roll():
    value = randint(1, 6)
    if value == 6:
        raise ValueError("Unlucky roll: 6 triggered an exception!")
    return value

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)