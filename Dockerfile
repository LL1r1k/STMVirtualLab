FROM ubuntu:18.04

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
    # Development files
        build-essential \
        git \
        bzip2 \
        curl \
        openocd \
        python3 \
        python3-pip \
        wget && \
    apt-get clean 

# ARM GCC, GDB, AS, LD
RUN wget -qO- https://developer.arm.com/-/media/Files/downloads/gnu-rm/9-2019q4/gcc-arm-none-eabi-9-2019-q4-major-x86_64-linux.tar.bz2 | tar -xj
ENV PATH "/gcc-arm-none-eabi-9-2019-q4-major/bin:$PATH"

COPY . /STMVirtualLab

WORKDIR /STMVirtualLab

# Yarn
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - && \
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list && \
    apt-get update && \
    apt-get install -y yarn && \
    yarn install --ignore-engines && \
    yarn build 

# Python requirements
RUN pip3 install -U pip && \
    pip3 install -r requirements.txt

CMD ["python3", "-m", "gdbgui"]