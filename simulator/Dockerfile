FROM python:3.12-slim
WORKDIR /app
COPY compressor.py server.py ./
EXPOSE 8000
HEALTHCHECK --interval=2s --timeout=2s --retries=15 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["python", "server.py"]
