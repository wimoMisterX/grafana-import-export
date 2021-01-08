FROM python:3.8-slim-buster
RUN pip install requests
COPY grafana_import_export.py /
ENTRYPOINT ["python", "grafana_import_export.py"]
