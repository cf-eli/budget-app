FROM python:3.12

RUN apt-get update -qqy \
  && apt-get -qqy --no-install-recommends install \
    curl \
    libpq-dev \
    tesseract-ocr \                
    tesseract-ocr-eng \            
    libtesseract-dev \             
  && pip install --no-cache-dir setuptools \
    wheel \
  && pip install --no-cache-dir \
    "poetry>=1.0,<2.0"


ENV HOME=/home/appuser
ENV PATH=$HOME/.local/bin:$PATH
RUN mkdir -p $HOME/.local/bin \
    && groupadd -g 1000 appuser \
    && useradd -r -u 1000 -g appuser appuser \
    && chown -R appuser $HOME
USER appuser
WORKDIR $HOME



RUN pip install --user pbr

# Install the poetry-plugin-export to ensure future compatibility
RUN poetry self add poetry-plugin-export

# Copy only requirements to cache them in docker layer
RUN mkdir -p build/src/
COPY --chown=appuser:appuser pyproject.toml poetry.lock build/
COPY --chown=appuser:appuser src/ build/src/

RUN cd build/ \
    && poetry export --without-hashes -o requirements.txt \
    && cd ..


# Install all requirements globally from build as index
RUN pip install --user -r build/requirements.txt build/\
    && rm -rf build/

    COPY --chown=appuser:appuser asgi.py entrypoint.sh ./
RUN chmod +x entrypoint.sh

ARG PORT=8085

ENV HOST=0.0.0.0
ENV PORT=${PORT}

ENTRYPOINT ["./entrypoint.sh"]
CMD ["serve"]

EXPOSE ${PORT}
