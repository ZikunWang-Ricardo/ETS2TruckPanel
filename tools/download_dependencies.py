"""Download pinned official release inputs; verify content before use."""
import hashlib
import io
from pathlib import Path
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FILES={
    'NotoSansCJKsc-Regular.otf':('https://raw.githubusercontent.com/notofonts/noto-cjk/Sans2.004/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf','2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b'),
    'python-3.13.12-embed-amd64.zip':('https://www.python.org/ftp/python/3.13.12/python-3.13.12-embed-amd64.zip','76f238f606250c87c6beac75dccd35ee99070a13490555936abb6cb64ecce3d0'),
    'release_v_1_12_1.zip':('https://github.com/RenCloud/scs-sdk-plugin/releases/download/V.1.12.1/release_v_1_12_1.zip',None),
    'scs-telemetry-common.hpp':('https://raw.githubusercontent.com/RenCloud/scs-sdk-plugin/V.1.12.1/scs-telemetry/inc/scs-telemetry-common.hpp','8e195082bde8876aa5906da8f9bea835bdd7440ee444c308887be52a0f35fbd4'),
}


def main():
    vendor=ROOT/'vendor';vendor.mkdir(exist_ok=True)
    for name,(url,digest) in FILES.items():
        p=vendor/name
        data=p.read_bytes() if p.exists() else urllib.request.urlopen(url,timeout=90).read()
        if digest and hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Checksum mismatch: '+name)
        p.write_bytes(data)
        if name=='release_v_1_12_1.zip':
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                path='release_v_1_12_1/Win64/scs-telemetry.dll';dll=z.read(path)
                if hashlib.sha256(dll).hexdigest()!='1d03dbc7a975e72203c60a7b9998021ceb8800b836bf28a131279979ad386cd4':raise ValueError('SDK checksum mismatch')
                dest=vendor/'rencloud'/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(dll)
        print('Verified',name)


if __name__=='__main__':main()
