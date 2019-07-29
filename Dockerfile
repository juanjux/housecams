FROM python:3.7-slim-buster
MAINTAINER Juanjo Alvarez <juanjo@juanjoalvarez.net>

# Install dlib dependencies
RUN apt-get -y update
RUN apt-get install -y --fix-missing \
    build-essential \
    cmake \
    gfortran \
    git \
    wget \
    unzip \
    yasm \
    curl \
    graphicsmagick \
    libgraphicsmagick1-dev \
    libatlas-base-dev \
    libavcodec-dev \
    libavformat-dev \
    libgtk2.0-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    liblapack-dev \
    libswscale-dev \
    libtbb2 \
    libtbb-dev \
    libpq-dev \
    pkg-config \
    python3-dev \
    python3-numpy \
    python3-opencv \
    software-properties-common \
    zip \
    && apt-get clean && rm -rf /tmp/* /var/tmp/*

RUN cp /usr/lib/python3/dist-packages/cv2.cpython-37m-x86_64-linux-gnu.so \
       /usr/local/lib/python3.7/site-packages/

# Compile and install dlib
RUN cd ~ && \
    mkdir -p dlib && \
    git clone -b 'v19.17' --single-branch https://github.com/davisking/dlib.git dlib/ && \
    cd  dlib/ && \
    python3 setup.py install
    # For PCs:
    #python3 setup.py install --yes USE_AVX_INSTRUCTIONS

RUN ln -s \
  /usr/local/python/cv2/python-3.7/cv2.cpython-37m-x86_64-linux-gnu.so \
  /usr/local/lib/python3.7/site-packages/cv2.so

RUN pip3 install face_recognition

WORKDIR ./src

COPY . .

ENTRYPOINT [ "python", "./src/facerec.py", "/faces" ]
