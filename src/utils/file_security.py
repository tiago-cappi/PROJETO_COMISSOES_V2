"""
Módulo de segurança para operações de arquivo.
Implementa: File Locking, Atomic Backups, SHA256 Hashing, Read-Only toggling.
"""

import os
import shutil
import hashlib
import stat
from datetime import datetime
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FileSecurityManager:
    """
    Gerencia segurança de arquivos: backups, integridade, e controle de acesso.
    """

    def __init__(self, backup_dir: Optional[str] = None):
        """
        Inicializa o gerenciador de segurança.

        Args:
            backup_dir: Diretório para backups. Se None, usa '<dir_arquivo>/backups'.
        """
        self.backup_dir = backup_dir

    def is_file_locked(self, filepath: str) -> bool:
        """
        Verifica se um arquivo está aberto/bloqueado por outro processo.
        
        NOTA: Este método primeiro remove o atributo Read-Only temporariamente
        para testar se o arquivo está realmente bloqueado por outro processo,
        e não apenas marcado como somente leitura.

        Args:
            filepath: Caminho do arquivo a verificar.

        Returns:
            True se o arquivo está bloqueado por outro processo, False caso contrário.
        """
        if not os.path.exists(filepath):
            return False

        # Salvar o modo original para restaurar depois
        original_mode = None
        try:
            original_mode = os.stat(filepath).st_mode
            
            # Temporariamente remover Read-Only se estiver ativo
            if not (original_mode & stat.S_IWRITE):
                os.chmod(filepath, original_mode | stat.S_IWRITE)
        except Exception:
            pass

        try:
            # Tenta abrir o arquivo em modo exclusivo de escrita
            with open(filepath, 'r+b') as f:
                # No Windows, tentar bloquear o arquivo
                try:
                    import msvcrt
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                except (ImportError, OSError):
                    # Se não for Windows ou falhar, tenta método alternativo
                    pass
            return False
        except (IOError, OSError, PermissionError):
            return True
        finally:
            # Restaurar o modo original (Read-Only se era antes)
            if original_mode is not None:
                try:
                    os.chmod(filepath, original_mode)
                except Exception:
                    pass

    def create_backup(self, filepath: str) -> Tuple[bool, str]:
        """
        Cria um backup atômico do arquivo com timestamp.

        Args:
            filepath: Caminho do arquivo a fazer backup.

        Returns:
            Tuple (sucesso: bool, caminho_backup: str ou mensagem_erro: str)
        """
        if not os.path.exists(filepath):
            return True, "Arquivo não existe, backup não necessário."

        try:
            # Determinar diretório de backup
            if self.backup_dir:
                backup_directory = self.backup_dir
            else:
                backup_directory = os.path.join(os.path.dirname(filepath), "backups")

            # Criar diretório de backup se não existir
            os.makedirs(backup_directory, exist_ok=True)

            # Gerar nome do backup com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(filepath)
            name, ext = os.path.splitext(filename)
            backup_filename = f"{name}.bak.{timestamp}{ext}"
            backup_path = os.path.join(backup_directory, backup_filename)

            # Copiar arquivo
            shutil.copy2(filepath, backup_path)

            logger.info(f"[SECURITY] Backup criado: {backup_path}")
            return True, backup_path

        except Exception as e:
            error_msg = f"Falha ao criar backup: {str(e)}"
            logger.error(f"[SECURITY] {error_msg}")
            return False, error_msg

    def restore_backup(self, backup_path: str, target_path: str) -> Tuple[bool, str]:
        """
        Restaura um arquivo a partir de um backup.

        Args:
            backup_path: Caminho do arquivo de backup.
            target_path: Caminho de destino para restauração.

        Returns:
            Tuple (sucesso: bool, mensagem: str)
        """
        try:
            if not os.path.exists(backup_path):
                return False, f"Backup não encontrado: {backup_path}"

            shutil.copy2(backup_path, target_path)
            logger.info(f"[SECURITY] Backup restaurado: {backup_path} -> {target_path}")
            return True, f"Backup restaurado com sucesso."

        except Exception as e:
            error_msg = f"Falha ao restaurar backup: {str(e)}"
            logger.error(f"[SECURITY] {error_msg}")
            return False, error_msg

    def calculate_hash(self, filepath: str) -> Tuple[bool, str]:
        """
        Calcula o hash SHA256 de um arquivo.

        Args:
            filepath: Caminho do arquivo.

        Returns:
            Tuple (sucesso: bool, hash_hex: str ou mensagem_erro: str)
        """
        if not os.path.exists(filepath):
            return False, "Arquivo não existe."

        try:
            sha256_hash = hashlib.sha256()
            with open(filepath, "rb") as f:
                # Ler em blocos para arquivos grandes
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)

            hash_hex = sha256_hash.hexdigest()
            return True, hash_hex

        except Exception as e:
            error_msg = f"Falha ao calcular hash: {str(e)}"
            logger.error(f"[SECURITY] {error_msg}")
            return False, error_msg

    def save_hash(self, filepath: str, hash_value: str) -> Tuple[bool, str]:
        """
        Salva o hash em um arquivo .hash associado.

        Args:
            filepath: Caminho do arquivo original.
            hash_value: Valor do hash a salvar.

        Returns:
            Tuple (sucesso: bool, mensagem: str)
        """
        try:
            hash_filepath = f"{filepath}.hash"
            with open(hash_filepath, "w", encoding="utf-8") as f:
                f.write(f"{hash_value}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write(f"File: {os.path.basename(filepath)}\n")

            logger.info(f"[SECURITY] Hash salvo: {hash_filepath}")
            return True, hash_filepath

        except Exception as e:
            error_msg = f"Falha ao salvar hash: {str(e)}"
            logger.error(f"[SECURITY] {error_msg}")
            return False, error_msg

    def verify_hash(self, filepath: str) -> Tuple[bool, str]:
        """
        Verifica se o hash do arquivo corresponde ao hash salvo.

        Args:
            filepath: Caminho do arquivo a verificar.

        Returns:
            Tuple (válido: bool, mensagem: str)
        """
        hash_filepath = f"{filepath}.hash"

        if not os.path.exists(hash_filepath):
            return True, "Arquivo de hash não existe, verificação ignorada."

        try:
            # Ler hash salvo
            with open(hash_filepath, "r", encoding="utf-8") as f:
                saved_hash = f.readline().strip()

            # Calcular hash atual
            success, current_hash = self.calculate_hash(filepath)
            if not success:
                return False, current_hash

            # Comparar
            if saved_hash == current_hash:
                logger.info(f"[SECURITY] Integridade verificada: {filepath}")
                return True, "Integridade verificada com sucesso."
            else:
                warning_msg = f"ALERTA: Hash não corresponde! Arquivo pode ter sido modificado manualmente."
                logger.warning(f"[SECURITY] {warning_msg}")
                return False, warning_msg

        except Exception as e:
            error_msg = f"Falha ao verificar hash: {str(e)}"
            logger.error(f"[SECURITY] {error_msg}")
            return False, error_msg

    def set_read_only(self, filepath: str, read_only: bool = True) -> Tuple[bool, str]:
        """
        Define ou remove o atributo de somente leitura do arquivo.

        Args:
            filepath: Caminho do arquivo.
            read_only: True para definir como somente leitura, False para remover.

        Returns:
            Tuple (sucesso: bool, mensagem: str)
        """
        if not os.path.exists(filepath):
            return False, "Arquivo não existe."

        try:
            current_mode = os.stat(filepath).st_mode

            if read_only:
                # Remover permissão de escrita
                new_mode = current_mode & ~stat.S_IWRITE
                action = "definido como somente leitura"
            else:
                # Adicionar permissão de escrita
                new_mode = current_mode | stat.S_IWRITE
                action = "permissão de escrita restaurada"

            os.chmod(filepath, new_mode)
            logger.info(f"[SECURITY] Arquivo {action}: {filepath}")
            return True, f"Arquivo {action}."

        except Exception as e:
            error_msg = f"Falha ao alterar permissões: {str(e)}"
            logger.error(f"[SECURITY] {error_msg}")
            return False, error_msg

    def cleanup_old_backups(self, backup_dir: str, keep_count: int = 30) -> int:
        """
        Remove backups antigos, mantendo apenas os N mais recentes.

        Args:
            backup_dir: Diretório de backups.
            keep_count: Quantidade de backups a manter.

        Returns:
            Número de backups removidos.
        """
        if not os.path.exists(backup_dir):
            return 0

        try:
            # Listar todos os arquivos de backup
            backup_files = []
            for f in os.listdir(backup_dir):
                if ".bak." in f:
                    full_path = os.path.join(backup_dir, f)
                    if os.path.isfile(full_path):
                        backup_files.append((full_path, os.path.getmtime(full_path)))

            # Ordenar por data de modificação (mais recente primeiro)
            backup_files.sort(key=lambda x: x[1], reverse=True)

            # Remover os mais antigos
            removed_count = 0
            for filepath, _ in backup_files[keep_count:]:
                try:
                    os.remove(filepath)
                    removed_count += 1
                    logger.info(f"[SECURITY] Backup antigo removido: {filepath}")
                except Exception:
                    pass

            return removed_count

        except Exception as e:
            logger.error(f"[SECURITY] Falha ao limpar backups: {str(e)}")
            return 0
