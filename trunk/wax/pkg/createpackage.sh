#!/bin/sh

rm -rf tmp

cd ..
rm -rf build
python setup.py bdist --plat-name all
cd pkg

mkdir tmp
mkdir tmp/CONTROL
cp control tmp/CONTROL

# tar contents into pkg dir
tar -C tmp -xvzf ../dist/wax*all.tar.gz

chown -R root:root tmp

# If Python version installed on system builder is 2.5
mv tmp/usr/lib/python2.5/ tmp/usr/lib/python2.7

# If Python version installed on system builder is 2.6
mkdir tmp/usr/lib/
mv tmp/usr/local/* tmp/usr/
rm -Rf tmp/usr/local/
mv tmp/usr/lib/python2.7/dist-packages tmp/usr/lib/python2.7/site-packages

# make ipk
./ipkg-build tmp

#rm -rf tmp
