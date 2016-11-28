FROM rocker/r-base

# ensure local python is preferred over distribution python
ENV PATH /usr/local/bin:$PATH

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG C.UTF-8

RUN set -ex \
  && buildDeps=' \
      python3-dev \
      python3-setuptools \
      python3-pip \
      python3-pandas \
      python3-virtualenv \
      libopenblas-base \
  ' \
  && apt-get update && apt-get install -y $buildDeps --no-install-recommends && rm -rf /var/lib/apt/lists/* \
  && R --vanilla -e 'install.packages("survey", repos="http://R-Forge.R-project.org")'

RUN mkdir -p /app
WORKDIR /app

EXPOSE 7777

COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /app

CMD ["python3", "./test_harness.py"]
