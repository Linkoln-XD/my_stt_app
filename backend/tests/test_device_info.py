import sys
import types

from app.services.device_info import detect_gpu_backend, gpu_available


def _install_fake_torch(monkeypatch, *, cuda: bool, mps: bool):
    fake = types.ModuleType("torch")

    class Cuda:
        @staticmethod
        def is_available():
            return cuda

    class Mps:
        @staticmethod
        def is_available():
            return mps

    fake.cuda = Cuda
    fake.backends = types.SimpleNamespace(mps=Mps())
    monkeypatch.setitem(sys.modules, "torch", fake)


def test_detect_cuda_preferred(monkeypatch):
    _install_fake_torch(monkeypatch, cuda=True, mps=True)
    assert detect_gpu_backend() == "cuda"
    assert gpu_available() is True


def test_detect_mps_when_no_cuda(monkeypatch):
    _install_fake_torch(monkeypatch, cuda=False, mps=True)
    assert detect_gpu_backend() == "mps"
    assert gpu_available() is True


def test_detect_none(monkeypatch):
    _install_fake_torch(monkeypatch, cuda=False, mps=False)
    assert detect_gpu_backend() == "none"
    assert gpu_available() is False
