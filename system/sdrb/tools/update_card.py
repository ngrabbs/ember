"""Apply the verified CAN candidate to the identified, backed-up SDRB card.

Run on m75q as root after unmounted filesystem checks. No raw image write,
rootfs replacement, account change, or existing runtime-library replacement.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

RUN = Path('/media/ngrabbs/BACKUP-A/ember-sdrb-20261003-card01')
SOURCE = Path('/media/ngrabbs/BACKUP-A/sdrb-uhd-linux-20260916/can-dual-01')
VERSION = '6.6.40-xilinx-gd37e591b96e0'
OLD = {
    'BOOT.BIN': 'e65252d73d9d40f15caff930d085f8aa1d67b2c37668ce91e5a01d9fbe73d47a',
    'image.ub': '992e4f2b98834e7b1000c027ddc89fe10219719a636c370d032183c14b42428e',
    'boot.scr': '4c7ed60cad10872084bf727b2c9ab0eca9eab992635cf3abf67dfe7ed9cc7807',
}
NEW = {
    'BOOT.BIN': 'd77ca4e55841b9eee95b06f30b8066d096eb8139af9e94ea5ef9bc5d50158620',
    'image.ub': '4373833ccb9975e51e2a90fab0a886a9610514e3502879c785c58184f5db8741',
    'boot.scr': OLD['boot.scr'],
}
ARCHIVE_HASH = 'a4178024909ee39e7b422cab05b02d1783b1445d7d1064b3ae9a24f7d52b6ae8'
ADAPTER_SOURCE = Path('/home/ngrabbs/work/ember-sdrb-adapter-20261003/ground/ember')
ADAPTER_FILES = ('sdrb_can.py', 'codec.py', 'dictionary.json', 'comms_uart.py')
ADAPTER_DEST = Path('home/petalinux/ember-can-monitor-20261003')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def snapshot(root, names):
    result = {}
    for name in names:
        p = root/name
        result[name] = ('link:' + os.readlink(p)) if p.is_symlink() else sha(p)
    return result


def mount(part, dest, readonly):
    options = 'ro,noload' if readonly and part.endswith('2') else 'ro' if readonly else 'rw'
    subprocess.run(['mount', '-o', options, part, str(dest)], check=True)


def main():
    assert os.geteuid() == 0
    assert Path('/sys/block/sdb/removable').read_text().strip() == '1'
    assert int(subprocess.check_output(['blockdev', '--getsize64', '/dev/sdb'])) == 15523119104
    assert subprocess.check_output(['blkid', '-s', 'UUID', '-o', 'value', '/dev/sdb2'], text=True).strip() == 'ffedbcdf-0312-433c-b97a-36db82bc4a78'
    backup = json.loads((RUN/'backup.json').read_text())
    assert backup['decompressed_backup_verified'] and backup['bytes'] == 15523119104
    assert (RUN/'before.img.gz').is_file()
    checks = json.loads((RUN/'filesystem-check.json').read_text())
    assert checks['fat_rc'] == checks['ext4_final_rc'] == 0
    for part in ('/dev/sdb1', '/dev/sdb2'):
        assert not subprocess.run(['findmnt', '-rn', '-S', part], capture_output=True).stdout
    for name, expected in NEW.items():
        assert sha(SOURCE/'bootfiles'/name) == expected
    archive = SOURCE/'card-update/kernel-modules.tar.gz'
    assert sha(archive) == ARCHIVE_HASH
    stage = RUN/'staged-modules'
    stage.mkdir(exist_ok=False)
    with tarfile.open(archive) as tar:
        members = tar.getmembers()
        for member in members:
            p = Path(member.name)
            assert '..' not in p.parts and not p.is_absolute()
            assert p.parts[:4] == ('usr', 'lib', 'modules', VERSION)
            assert member.isdir() or member.isfile()  # verified archive has no links
        tar.extractall(stage, filter='data')
    boot, root = RUN/'mount-boot', RUN/'mount-root'
    boot.mkdir(exist_ok=False); root.mkdir(exist_ok=False)
    names = list(json.loads((SOURCE/'checks/card-rootfs-compatibility.json').read_text())['checked'])
    names = [n for n in names if '/modules/' not in n]
    names += ['etc/passwd', 'etc/shadow', 'etc/group', 'etc/gshadow']
    mounted = []
    try:
        for part, dest in (('/dev/sdb1', boot), ('/dev/sdb2', root)):
            mount(part, dest, True); mounted.append(dest)
        assert not (root/'usr/lib').is_symlink()
        assert {n: sha(boot/n) for n in OLD} == OLD
        account = next(line.split(':') for line in (root/'etc/passwd').read_text().splitlines() if line.startswith('petalinux:'))
        assert account[5] == '/home/petalinux'
        uid, gid = int(account[2]), int(account[3])
        assert (root/'home/petalinux').is_dir() and not (root/'home/petalinux').is_symlink()
        assert not (root/ADAPTER_DEST).exists()
        adapter_hashes = {n: sha(ADAPTER_SOURCE/n) for n in ADAPTER_FILES}
        before = snapshot(root, names)
        old_modules = [str(p.relative_to(root)) for p in (root/'usr/lib/modules').rglob('*') if p.is_file() or p.is_symlink()]
        old_module_hashes = snapshot(root, old_modules)
        (RUN/'preserved-before.json').write_text(json.dumps(before, indent=2)+'\n')
        (RUN/'old-modules-before.json').write_text(json.dumps(old_module_hashes, indent=2)+'\n')
        backup_boot = RUN/'boot-before-current'; backup_boot.mkdir(exist_ok=False)
        for n in OLD:
            shutil.copy2(boot/n, backup_boot/n)
        files = [p for p in stage.rglob('*') if p.is_file()]
        for p in files:
            relative = p.relative_to(stage); target = root/relative
            assert all(not ancestor.is_symlink() for ancestor in target.parents if ancestor != root)
            assert not target.is_symlink()
            if target.exists():
                assert sha(target) == sha(p), str(target)
        for dest in reversed(mounted):
            subprocess.run(['umount', str(dest)], check=True)
        mounted.clear()
        for part, dest in (('/dev/sdb1', boot), ('/dev/sdb2', root)):
            mount(part, dest, False); mounted.append(dest)
        for p in files:
            target = root/p.relative_to(stage)
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, target)
        adapter = root/ADAPTER_DEST
        adapter.mkdir(mode=0o755)
        os.chown(adapter, uid, gid)
        for n in ADAPTER_FILES:
            shutil.copyfile(ADAPTER_SOURCE/n, adapter/n)
            os.chown(adapter/n, uid, gid)
            os.chmod(adapter/n, 0o644)
        for n, h in NEW.items():
            if sha(boot/n) == h:
                continue
            temp = boot/(n+'.ember-can-new')
            assert not temp.exists()
            shutil.copyfile(SOURCE/'bootfiles'/n, temp)
            with temp.open('rb') as f:
                os.fsync(f.fileno())
            assert sha(temp) == h
            os.replace(temp, boot/n)
        subprocess.run(['sync'], check=True)
        for dest in reversed(mounted):
            subprocess.run(['umount', str(dest)], check=True)
        mounted.clear()
        for part, dest in (('/dev/sdb1', boot), ('/dev/sdb2', root)):
            mount(part, dest, True); mounted.append(dest)
        assert {n: sha(boot/n) for n in NEW} == NEW
        assert snapshot(root, names) == before
        assert snapshot(root, old_modules) == old_module_hashes
        for p in files:
            assert sha(root/p.relative_to(stage)) == sha(p)
        assert {n: sha(root/ADAPTER_DEST/n) for n in ADAPTER_FILES} == adapter_hashes
        (RUN/'update-result.json').write_text(json.dumps({
            'status': 'PASS_REMOUNTED_READBACK', 'boot_sha256': NEW,
            'kernel': VERSION, 'module_files_verified': len(files),
            'runtime_and_account_entries_preserved': len(before),
            'old_module_entries_preserved': len(old_modules),
            'current_uhd_sha256_preserved': before['usr/lib/libuhd.so.4.8.0'],
            'rootfs_replaced': False, 'rf_tested': False,
            'optional_adapter_directory': str(ADAPTER_DEST),
            'optional_adapter_sha256': adapter_hashes, 'startup_services_added': False,
            'board_boot_tested': False, 'full_backup': str(RUN/'before.img.gz')}, indent=2)+'\n')
        print('PASS: boot/module update and preserved runtime verified after remount', flush=True)
    finally:
        for dest in reversed(mounted):
            subprocess.run(['umount', str(dest)], check=True)


if __name__ == '__main__':
    main()
