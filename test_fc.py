"""Tests for fastc core logic."""
import importlib.util
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

# Import the fc script as a module (no .py extension)
_fc_path = str(Path(__file__).parent / "fc")
_loader = SourceFileLoader("fc", _fc_path)
_spec = importlib.util.spec_from_loader("fc", _loader, origin=_fc_path)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["fc"] = _mod
_spec.loader.exec_module(_mod)

# Pull out functions and constants under test
is_lockfile = _mod.is_lockfile
is_binary_path = _mod.is_binary_path
git_unquote = _mod.git_unquote
strip_diff_noise = _mod.strip_diff_noise
strip_diff_context = _mod.strip_diff_context
_phase2_plan = _mod._phase2_plan
extract_diff_path = _mod.extract_diff_path
try_repair_json = _mod.try_repair_json
normalize_llm_files = _mod.normalize_llm_files
is_echoing_keys = _mod.is_echoing_keys
_clean_commit_message = _mod._clean_commit_message
validate_and_fix_commits = _mod.validate_and_fix_commits
detect_directory_moves = _mod.detect_directory_moves
normalize_llm_result = _mod.normalize_llm_result
is_malformed_response = _mod.is_malformed_response
compress_diff = _mod.compress_diff
BINARY_EXTENSIONS = _mod.BINARY_EXTENSIONS
summarize_file_operations = _mod.summarize_file_operations
group_files_by_directory = _mod.group_files_by_directory
is_file_deleted = _mod.is_file_deleted
_dir_scope = _mod._dir_scope
_smart_path_label = _mod._smart_path_label
compute_path_context = _mod.compute_path_context
_ensure_grounded_scope = _mod._ensure_grounded_scope


# ---------------------------------------------------------------------------
# is_lockfile
# ---------------------------------------------------------------------------

class TestIsLockfile:
    def test_pnpm_lock(self):
        assert is_lockfile("pnpm-lock.yaml")

    def test_nested_pnpm_lock(self):
        assert is_lockfile("apps/web/pnpm-lock.yaml")

    def test_package_lock(self):
        assert is_lockfile("package-lock.json")

    def test_cargo_lock(self):
        assert is_lockfile("Cargo.lock")

    def test_go_sum(self):
        assert is_lockfile("go.sum")

    def test_poetry_lock(self):
        assert is_lockfile("poetry.lock")

    def test_bun_lockb(self):
        assert is_lockfile("bun.lockb")

    def test_minified_js(self):
        assert is_lockfile("dist/bundle.min.js")

    def test_minified_css(self):
        assert is_lockfile("styles/app.min.css")

    def test_source_map(self):
        assert is_lockfile("dist/bundle.js.map")

    def test_regular_file(self):
        assert not is_lockfile("src/main.py")

    def test_similar_name(self):
        assert not is_lockfile("lockfile.txt")

    def test_yaml_not_lock(self):
        assert not is_lockfile("config.yaml")

    def test_json_not_lock(self):
        assert not is_lockfile("package.json")


# ---------------------------------------------------------------------------
# is_binary_path
# ---------------------------------------------------------------------------

class TestIsBinaryPath:
    @pytest.mark.parametrize("ext", [
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp",
        ".pdf", ".exe", ".zip", ".tar", ".gz", ".pyc",
        ".woff", ".woff2", ".ttf", ".mp3", ".mp4",
    ])
    def test_binary_extensions(self, ext):
        assert is_binary_path(f"file{ext}")

    def test_svg_is_not_binary(self):
        assert not is_binary_path("icon.svg")

    @pytest.mark.parametrize("path", [
        "main.py", "index.ts", "README.md", "Makefile", "go.mod",
    ])
    def test_text_files(self, path):
        assert not is_binary_path(path)

    def test_no_extension(self):
        assert not is_binary_path("Makefile")

    def test_case_insensitive(self):
        assert is_binary_path("photo.PNG")
        assert is_binary_path("archive.ZIP")

    def test_nested_path(self):
        assert is_binary_path("assets/images/logo.png")


# ---------------------------------------------------------------------------
# git_unquote
# ---------------------------------------------------------------------------

class TestGitUnquote:
    def test_plain_path(self):
        assert git_unquote("src/main.py") == "src/main.py"

    def test_quoted_ascii(self):
        assert git_unquote('"src/main.py"') == "src/main.py"

    def test_escaped_newline(self):
        assert git_unquote('"file\\nname"') == "file\nname"

    def test_escaped_tab(self):
        assert git_unquote('"file\\tname"') == "file\tname"

    def test_escaped_backslash(self):
        assert git_unquote('"path\\\\file"') == "path\\file"

    def test_escaped_quote(self):
        assert git_unquote('"say\\"hello\\""') == 'say"hello"'

    def test_octal_utf8(self):
        # ñ in UTF-8 is \303\261
        result = git_unquote('"espa\\303\\261a"')
        assert result == "españa"

    def test_escaped_bell(self):
        assert git_unquote('"x\\ay"') == "x\ay"

    def test_escaped_backspace(self):
        assert git_unquote('"x\\by"') == "x\by"

    def test_escaped_formfeed(self):
        assert git_unquote('"x\\fy"') == "x\fy"

    def test_escaped_carriage_return(self):
        assert git_unquote('"x\\ry"') == "x\ry"

    def test_escaped_vtab(self):
        assert git_unquote('"x\\vy"') == "x\vy"


# ---------------------------------------------------------------------------
# strip_diff_noise
# ---------------------------------------------------------------------------

class TestStripDiffNoise:
    def test_removes_index_lines(self):
        diff = "index abc123..def456 100644\n+added line"
        assert "index " not in strip_diff_noise(diff)
        assert "+added line" in strip_diff_noise(diff)

    def test_removes_similarity_index(self):
        diff = "similarity index 95%\nrename from a\nrename to b"
        result = strip_diff_noise(diff)
        assert "similarity index" not in result
        assert "rename from a" in result

    def test_removes_dissimilarity_index(self):
        diff = "dissimilarity index 50%\n+new content"
        result = strip_diff_noise(diff)
        assert "dissimilarity index" not in result

    def test_preserves_diff_content(self):
        diff = "diff --git a/f b/f\n--- a/f\n+++ b/f\n@@ -1 +1 @@\n-old\n+new"
        result = strip_diff_noise(diff)
        assert result == diff

    def test_empty_input(self):
        assert strip_diff_noise("") == ""


# ---------------------------------------------------------------------------
# strip_diff_context
# ---------------------------------------------------------------------------

class TestStripDiffContext:
    DIFF = (
        "diff --git a/f.py b/f.py\n"
        "--- a/f.py\n"
        "+++ b/f.py\n"
        "@@ -1,4 +1,4 @@\n"
        " def handler():\n"
        "-    return old()\n"
        "+    return new()\n"
        " # trailing context\n"
    )

    def test_drops_context_and_header_pair(self):
        assert strip_diff_context(self.DIFF).splitlines() == [
            "diff --git a/f.py b/f.py",
            "@@ -1,4 +1,4 @@",
            "-    return old()",
            "+    return new()",
        ]

    def test_keeps_changed_lines_starting_with_dashes(self):
        # A YAML separator being removed looks exactly like a file header.
        diff = (
            "diff --git a/c.yaml b/c.yaml\n"
            "--- a/c.yaml\n"
            "+++ b/c.yaml\n"
            "@@ -1,2 +1,2 @@\n"
            "----\n"
            "+++new\n"
        )
        assert strip_diff_context(diff).splitlines() == [
            "diff --git a/c.yaml b/c.yaml",
            "@@ -1,2 +1,2 @@",
            "----",
            "+++new",
        ]

    def test_keeps_file_operation_metadata(self):
        diff = "diff --git a/a b/b\nsimilarity index 95%\nrename from a\nrename to b\n"
        result = strip_diff_context(diff)
        assert "rename from a" in result
        assert "rename to b" in result
        assert "similarity index" not in result

    def test_empty_input(self):
        assert strip_diff_context("") == ""


# ---------------------------------------------------------------------------
# _phase2_plan
# ---------------------------------------------------------------------------

class TestPhase2Plan:
    CLAUDE = {"PROVIDER": _mod.PROVIDER_CLAUDE}
    OPENROUTER = {"PROVIDER": _mod.PROVIDER_OPENROUTER}

    def test_claude_single_file_asks_for_subject_only(self):
        prompt, fallback = _phase2_plan(self.CLAUDE, 1, "tightened the retry budget")
        assert "description" not in prompt
        assert fallback == "tightened the retry budget"

    def test_claude_multi_file_asks_for_a_description(self):
        prompt, fallback = _phase2_plan(self.CLAUDE, 2, "tightened the retry budget")
        assert "description" in prompt
        assert fallback == ""

    def test_openrouter_never_substitutes_the_hint(self):
        for n_files in (1, 2):
            prompt, fallback = _phase2_plan(self.OPENROUTER, n_files, "a hint")
            assert "description" in prompt
            assert fallback == ""


# ---------------------------------------------------------------------------
# extract_diff_path
# ---------------------------------------------------------------------------

class TestExtractDiffPath:
    def test_standard_header(self):
        assert extract_diff_path("diff --git a/src/main.py b/src/main.py") == "src/main.py"

    def test_rename_header(self):
        assert extract_diff_path("diff --git a/old/f.py b/new/f.py") == "new/f.py"

    def test_no_b_prefix(self):
        assert extract_diff_path("diff --git something") == ""

    def test_space_in_path(self):
        assert extract_diff_path("diff --git a/my file.py b/my file.py") == "my file.py"


# ---------------------------------------------------------------------------
# try_repair_json
# ---------------------------------------------------------------------------

class TestTryRepairJson:
    def test_valid_json_array(self):
        result = try_repair_json('[{"files":["a"],"message":"fix: a"}]')
        assert result == [{"files": ["a"], "message": "fix: a"}]

    def test_valid_json_object(self):
        result = try_repair_json('{"message":"fix: a"}')
        assert result == {"message": "fix: a"}

    def test_truncated_array(self):
        # Missing closing bracket
        result = try_repair_json('[{"files":["a"],"message":"fix: a"}')
        assert result is not None
        assert isinstance(result, list)

    def test_leading_garbage(self):
        result = try_repair_json('Here is the JSON:\n[{"files":["a"],"message":"fix: a"}]')
        assert result is not None
        assert isinstance(result, list)

    def test_trailing_garbage(self):
        result = try_repair_json('[{"files":["a"],"message":"fix: a"}]\nDone!')
        assert result is not None

    def test_completely_invalid(self):
        result = try_repair_json("this is not json at all")
        assert result is None

    def test_empty_string(self):
        result = try_repair_json("")
        assert result is None

    def test_markdown_fences_stripped_before_call(self):
        # Markdown fences are stripped in call_llm_raw, but test repair with them
        result = try_repair_json('```json\n[{"files":["a"],"message":"fix: a"}]\n```')
        # This might or might not work depending on repair logic
        # The important thing is it doesn't crash
        assert result is None or isinstance(result, (list, dict))


# ---------------------------------------------------------------------------
# normalize_llm_files
# ---------------------------------------------------------------------------

class TestNormalizeLlmFiles:
    def setup_method(self):
        self.staged = {
            "src/main.py": {"old": "src/main.py", "deleted": False},
            "src/utils.py": {"old": "lib/utils.py", "deleted": False},
            "README.md": {"old": "README.md", "deleted": False},
        }

    def test_exact_match(self):
        result = normalize_llm_files(["src/main.py"], self.staged)
        assert result == ["src/main.py"]

    def test_old_path_mapped(self):
        result = normalize_llm_files(["lib/utils.py"], self.staged)
        assert result == ["src/utils.py"]

    def test_unknown_file_dropped(self):
        result = normalize_llm_files(["nonexistent.py"], self.staged)
        assert result == []

    def test_non_list_returns_empty(self):
        result = normalize_llm_files("not a list", self.staged)
        assert result == []

    def test_non_string_items_dropped(self):
        result = normalize_llm_files([123, None, "src/main.py"], self.staged)
        assert result == ["src/main.py"]

    def test_leading_slash_stripped(self):
        result = normalize_llm_files(["/src/main.py"], self.staged)
        assert result == ["src/main.py"]

    def test_a_prefix_stripped(self):
        result = normalize_llm_files(["a/src/main.py"], self.staged)
        assert result == ["src/main.py"]

    def test_b_prefix_stripped(self):
        result = normalize_llm_files(["b/src/main.py"], self.staged)
        assert result == ["src/main.py"]

    def test_deduplication(self):
        result = normalize_llm_files(["src/main.py", "src/main.py"], self.staged)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# is_echoing_keys
# ---------------------------------------------------------------------------

class TestIsEchoingKeys:
    def test_valid_commit(self):
        commit = {"files": ["src/main.py"], "message": "fix: a", "description": "desc"}
        assert not is_echoing_keys(commit)

    def test_echoing_files(self):
        assert is_echoing_keys({"files": "files", "message": "fix: a"})

    def test_echoing_message(self):
        assert is_echoing_keys({"files": ["a"], "message": "message"})

    def test_echoing_description(self):
        assert is_echoing_keys({"files": ["a"], "message": "fix: a", "description": "description"})

    def test_missing_files(self):
        assert is_echoing_keys({"message": "fix: a"})

    def test_empty_files(self):
        assert is_echoing_keys({"files": [], "message": "fix: a"})

    def test_non_dict(self):
        assert is_echoing_keys("not a dict")
        assert is_echoing_keys(None)
        assert is_echoing_keys(42)

    def test_missing_message(self):
        assert is_echoing_keys({"files": ["a"]})

    def test_empty_message(self):
        assert is_echoing_keys({"files": ["a"], "message": ""})


# ---------------------------------------------------------------------------
# validate_and_fix_commits
# ---------------------------------------------------------------------------

class TestValidateAndFixCommits:
    def setup_method(self):
        self.staged = {
            "a.py": {"old": "a.py", "deleted": False},
            "b.py": {"old": "b.py", "deleted": False},
            "c.py": {"old": "c.py", "deleted": False},
        }

    def test_valid_commits(self):
        commits = [
            {"files": ["a.py", "b.py"], "message": "fix: ab"},
            {"files": ["c.py"], "message": "fix: c"},
        ]
        fixed, missing = validate_and_fix_commits(commits, self.staged)
        assert len(fixed) == 2
        assert missing == set()

    def test_missing_files_detected(self):
        commits = [{"files": ["a.py"], "message": "fix: a"}]
        fixed, missing = validate_and_fix_commits(commits, self.staged)
        assert missing == {"b.py", "c.py"}

    def test_malformed_commit_skipped(self):
        commits = [
            {"files": ["a.py"], "message": "fix: a"},
            "not a dict",
            {"no_files": True},
        ]
        fixed, missing = validate_and_fix_commits(commits, self.staged)
        assert len(fixed) == 1

    def test_all_echoing_keys_exits(self):
        commits = [{"files": "files", "message": "message"}]
        with pytest.raises(SystemExit):
            validate_and_fix_commits(commits, self.staged)

    def test_fallback_when_no_valid_commits(self):
        commits = [{"files": ["nonexistent.py"], "message": "fix: x"}]
        fixed, missing = validate_and_fix_commits(commits, self.staged)
        assert len(fixed) == 1
        assert fixed[0]["message"] == "chore: update files"


# ---------------------------------------------------------------------------
# normalize_llm_result
# ---------------------------------------------------------------------------

class TestNormalizeLlmResult:
    def test_list_passthrough(self):
        data = [{"files": ["a"], "message": "fix: a"}]
        assert normalize_llm_result(data) == data

    def test_dict_with_commits(self):
        data = {"commits": [{"files": ["a"], "message": "fix: a"}]}
        assert normalize_llm_result(data) == [{"files": ["a"], "message": "fix: a"}]

    def test_dict_with_groups(self):
        data = {"groups": [{"files": ["a"], "hint": "x"}]}
        assert normalize_llm_result(data) == [{"files": ["a"], "hint": "x"}]

    def test_single_commit_dict(self):
        data = {"files": ["a"], "message": "fix: a"}
        assert normalize_llm_result(data) == [data]

    def test_invalid_returns_empty(self):
        assert normalize_llm_result("string") == []
        assert normalize_llm_result(42) == []


# ---------------------------------------------------------------------------
# is_malformed_response
# ---------------------------------------------------------------------------

class TestIsMalformedResponse:
    def test_valid_response(self):
        assert not is_malformed_response([{"files": ["a"], "message": "fix: a"}])

    def test_non_list(self):
        assert is_malformed_response({"files": ["a"]})

    def test_empty_list(self):
        assert is_malformed_response([])

    def test_majority_echoing(self):
        result = [
            {"files": "files", "message": "message"},
            {"files": "files", "message": "message"},
            {"files": ["a.py"], "message": "fix: a"},
        ]
        assert is_malformed_response(result)


# ---------------------------------------------------------------------------
# detect_directory_moves
# ---------------------------------------------------------------------------

class TestDetectDirectoryMoves:
    def test_detects_directory_rename(self):
        staged = {
            "new/a.py": {"old": "old/a.py", "deleted": False},
            "new/b.py": {"old": "old/b.py", "deleted": False},
            "new/c.py": {"old": "old/c.py", "deleted": False},
        }
        moves = detect_directory_moves(staged)
        assert "new" in moves
        old_prefix, files = moves["new"]
        assert old_prefix == "old"
        assert len(files) == 3

    def test_ignores_single_renames(self):
        staged = {
            "new/a.py": {"old": "old/a.py", "deleted": False},
        }
        moves = detect_directory_moves(staged)
        assert len(moves) == 0

    def test_ignores_non_renames(self):
        staged = {
            "src/a.py": {"old": "src/a.py", "deleted": False},
            "src/b.py": {"old": "src/b.py", "deleted": False},
        }
        moves = detect_directory_moves(staged)
        assert len(moves) == 0

    def test_ignores_deleted(self):
        staged = {
            "new/a.py": {"old": "old/a.py", "deleted": True},
            "new/b.py": {"old": "old/b.py", "deleted": True},
            "new/c.py": {"old": "old/c.py", "deleted": True},
        }
        moves = detect_directory_moves(staged)
        assert len(moves) == 0


# ---------------------------------------------------------------------------
# Integration-like tests
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_lockfile_and_binary_no_overlap(self):
        """Lockfiles and binary extensions should be distinct categories."""
        lock_suffixes = {".min.js", ".min.css", ".map", ".lockb"}
        overlap = lock_suffixes & BINARY_EXTENSIONS
        # .lockb is intentionally in both (binary lockfile)
        assert overlap <= {".lockb"}

    def test_whitespace_only_diff(self):
        # splitlines() drops trailing empty line, so "\n\n" becomes ["", ""] -> "\n"
        result = strip_diff_noise("\n\n")
        assert result == "\n"

    def test_normalize_preserves_order_independence(self):
        staged = {
            "a.py": {"old": "a.py", "deleted": False},
            "b.py": {"old": "b.py", "deleted": False},
        }
        r1 = set(normalize_llm_files(["b.py", "a.py"], staged))
        r2 = set(normalize_llm_files(["a.py", "b.py"], staged))
        assert r1 == r2


# ---------------------------------------------------------------------------
# _clean_commit_message
# ---------------------------------------------------------------------------

class TestCleanCommitMessage:
    def test_strips_trailing_period(self):
        assert _clean_commit_message("feat: add thing.") == "feat: add thing"

    def test_strips_whitespace(self):
        assert _clean_commit_message("  fix: a  ") == "fix: a"

    def test_truncates_long_message(self):
        long_msg = "feat(scope): " + "x" * 100
        result = _clean_commit_message(long_msg)
        assert len(result) <= 72
        assert result.endswith("...")

    def test_preserves_short_message(self):
        msg = "fix(auth): correct token validation"
        assert _clean_commit_message(msg) == msg

    def test_exactly_72_chars_not_truncated(self):
        msg = "x" * 72
        assert _clean_commit_message(msg) == msg

    def test_73_chars_truncated(self):
        msg = "x" * 73
        result = _clean_commit_message(msg)
        assert len(result) == 72
        assert result.endswith("...")


# ---------------------------------------------------------------------------
# summarize_file_operations
# ---------------------------------------------------------------------------

class TestSummarizeFileOperations:
    def test_bulk_deletes_grouped(self):
        staged = {
            "old/a.py": {"old": "old/a.py", "deleted": True},
            "old/b.py": {"old": "old/b.py", "deleted": True},
            "old/c.py": {"old": "old/c.py", "deleted": True},
        }
        ops = summarize_file_operations(staged)
        assert len(ops) == 1
        assert "remove" in ops[0]["message"]

    def test_single_change(self):
        staged = {
            "src/main.py": {"old": "src/main.py", "deleted": False},
        }
        ops = summarize_file_operations(staged)
        assert len(ops) == 1
        assert ops[0]["files"] == ["src/main.py"]

    def test_mixed_operations(self):
        staged = {
            "src/a.py": {"old": "src/a.py", "deleted": False},
            "old/b.py": {"old": "old/b.py", "deleted": True},
        }
        ops = summarize_file_operations(staged)
        assert len(ops) == 2

    def test_empty_staged(self):
        ops = summarize_file_operations({})
        assert ops == []


# ---------------------------------------------------------------------------
# group_files_by_directory
# ---------------------------------------------------------------------------

class TestGroupFilesByDirectory:
    def test_returns_operations_when_available(self):
        staged = {
            "old/a.py": {"old": "old/a.py", "deleted": True},
            "old/b.py": {"old": "old/b.py", "deleted": True},
            "old/c.py": {"old": "old/c.py", "deleted": True},
        }
        groups = group_files_by_directory(staged)
        assert len(groups) >= 1
        all_files = set()
        for g in groups:
            all_files.update(g["files"])
        assert all_files == set(staged.keys())

    def test_fallback_single_group(self):
        # When summarize returns nothing, should get a single fallback group
        staged = {}
        groups = group_files_by_directory(staged)
        assert len(groups) == 1
        assert groups[0]["message"] == "chore: update files"


# ---------------------------------------------------------------------------
# is_file_deleted
# ---------------------------------------------------------------------------

class TestIsFileDeleted:
    def test_deleted_file(self):
        staged = {"a.py": {"old": "a.py", "deleted": True}}
        assert is_file_deleted("a.py", staged)

    def test_not_deleted(self):
        staged = {"a.py": {"old": "a.py", "deleted": False}}
        assert not is_file_deleted("a.py", staged)

    def test_missing_file(self):
        assert not is_file_deleted("nonexistent.py", {})

    def test_missing_deleted_key(self):
        staged = {"a.py": {"old": "a.py"}}
        assert not is_file_deleted("a.py", staged)


# ---------------------------------------------------------------------------
# _dir_scope
# ---------------------------------------------------------------------------

class TestDirScope:
    def test_monorepo_container_dir(self):
        assert _dir_scope("apps/grupeta/src/auth.ts") == "grupeta"

    def test_packages_container(self):
        assert _dir_scope("packages/shared/utils.ts") == "shared"

    def test_non_container_dir(self):
        assert _dir_scope("src/api/handler.go") == "src"

    def test_single_dir(self):
        assert _dir_scope("src/main.py") == "src"

    def test_root_file(self):
        assert _dir_scope("README.md") == ""

    def test_libs_container(self):
        assert _dir_scope("libs/core/index.ts") == "core"

    def test_crates_container(self):
        assert _dir_scope("crates/specl-eval/src/lib.rs") == "specl-eval"

    def test_tools_container(self):
        assert _dir_scope("tools/fastc/fc") == "fastc"


# ---------------------------------------------------------------------------
# _smart_path_label
# ---------------------------------------------------------------------------

class TestSmartPathLabel:
    def test_monorepo_deep_path(self):
        assert _smart_path_label("apps/grupeta/src/api/auth.ts") == "grupeta/auth.ts"

    def test_short_path_unchanged(self):
        assert _smart_path_label("src/main.py") == "src/main.py"

    def test_root_file(self):
        assert _smart_path_label("README.md") == "README.md"

    def test_non_container_deep_path(self):
        assert _smart_path_label("src/api/routes/handler.go") == "src/handler.go"

    def test_packages_deep_path(self):
        assert _smart_path_label("packages/shared/src/utils/format.ts") == "shared/format.ts"


# ---------------------------------------------------------------------------
# compute_path_context
# ---------------------------------------------------------------------------

class TestComputePathContext:
    def test_single_project(self):
        ctx = compute_path_context(["apps/grupeta/src/a.ts", "apps/grupeta/src/b.ts"])
        assert "grupeta" in ctx
        assert "PATH CONTEXT" in ctx

    def test_multi_project(self):
        ctx = compute_path_context(["apps/grupeta/a.ts", "packages/shared/b.ts"])
        assert "grupeta" in ctx
        assert "shared" in ctx

    def test_empty_paths(self):
        assert compute_path_context([]) == ""

    def test_root_only_files(self):
        ctx = compute_path_context(["README.md", "package.json"])
        assert ctx == ""

    def test_non_container_paths(self):
        ctx = compute_path_context(["src/api/a.go", "src/api/b.go"])
        assert "src" in ctx


# ---------------------------------------------------------------------------
# _ensure_grounded_scope
# ---------------------------------------------------------------------------

class TestEnsureGroundedScope:
    def test_adds_scope_when_missing(self):
        commit = {"files": ["apps/grupeta/src/auth.ts"], "message": "feat: add auth"}
        result = _ensure_grounded_scope(commit)
        assert result["message"] == "feat(grupeta): add auth"

    def test_preserves_existing_scope(self):
        commit = {"files": ["apps/grupeta/src/auth.ts"], "message": "feat(auth): add validation"}
        result = _ensure_grounded_scope(commit)
        assert result["message"] == "feat(auth): add validation"

    def test_no_scope_for_mixed_projects(self):
        commit = {"files": ["apps/grupeta/a.ts", "apps/other/b.ts"], "message": "chore: update deps"}
        result = _ensure_grounded_scope(commit)
        assert result["message"] == "chore: update deps"

    def test_scope_from_non_container(self):
        commit = {"files": ["src/api/handler.go", "src/api/routes.go"], "message": "fix: handle errors"}
        result = _ensure_grounded_scope(commit)
        assert result["message"] == "fix(src): handle errors"

    def test_no_files(self):
        commit = {"files": [], "message": "chore: update"}
        result = _ensure_grounded_scope(commit)
        assert result["message"] == "chore: update"

    def test_root_files_no_scope(self):
        commit = {"files": ["README.md"], "message": "docs: update readme"}
        result = _ensure_grounded_scope(commit)
        assert result["message"] == "docs: update readme"

    def test_non_conventional_message_unchanged(self):
        commit = {"files": ["apps/grupeta/a.ts"], "message": "WIP stuff"}
        result = _ensure_grounded_scope(commit)
        assert result["message"] == "WIP stuff"
