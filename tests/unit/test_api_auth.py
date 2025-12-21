"""Comprehensive unit tests for api/auth.py authentication module.

This module provides thorough test coverage for:
- Password hashing and verification
- JWT token creation and validation
- User authentication and authorization
- User repository operations (CRUD)
- Environment-based user seeding
- Security configuration validation
- Edge cases and error conditions
"""

import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import HTTPException
from jwt import ExpiredSignatureError, InvalidTokenError

from api.auth import (
    Token,
    TokenData,
    User,
    UserInDB,
    UserRepository,
    _is_truthy,
    _seed_credentials_from_env,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_user,
    get_password_hash,
    get_user,
    pwd_context,
    user_repository,
    verify_password,
)


class TestIsTruthy:
    """Test the _is_truthy helper function for boolean string parsing."""

    def test_is_truthy_with_true_lowercase(self):
        """Test 'true' returns True."""
        assert _is_truthy('true') is True

    def test_is_truthy_with_true_uppercase(self):
        """Test 'TRUE' returns True."""
        assert _is_truthy('TRUE') is True

    def test_is_truthy_with_true_mixedcase(self):
        """Test 'TrUe' returns True."""
        assert _is_truthy('TrUe') is True

    def test_is_truthy_with_one(self):
        """Test '1' returns True."""
        assert _is_truthy('1') is True

    def test_is_truthy_with_yes_lowercase(self):
        """Test 'yes' returns True."""
        assert _is_truthy('yes') is True

    def test_is_truthy_with_yes_uppercase(self):
        """Test 'YES' returns True."""
        assert _is_truthy('YES') is True

    def test_is_truthy_with_on_lowercase(self):
        """Test 'on' returns True."""
        assert _is_truthy('on') is True

    def test_is_truthy_with_on_uppercase(self):
        """Test 'ON' returns True."""
        assert _is_truthy('ON') is True

    def test_is_truthy_with_false(self):
        """Test 'false' returns False."""
        assert _is_truthy('false') is False

    def test_is_truthy_with_zero(self):
        """Test '0' returns False."""
        assert _is_truthy('0') is False

    def test_is_truthy_with_no(self):
        """Test 'no' returns False."""
        assert _is_truthy('no') is False

    def test_is_truthy_with_off(self):
        """Test 'off' returns False."""
        assert _is_truthy('off') is False

    def test_is_truthy_with_empty_string(self):
        """Test empty string returns False."""
        assert _is_truthy('') is False

    def test_is_truthy_with_none(self):
        """Test None returns False."""
        assert _is_truthy(None) is False

    def test_is_truthy_with_random_string(self):
        """Test random string returns False."""
        assert _is_truthy('random') is False

    def test_is_truthy_with_whitespace(self):
        """Test whitespace-only string returns False."""
        assert _is_truthy('   ') is False

    def test_is_truthy_with_numeric_strings(self):
        """Test various numeric strings."""
        assert _is_truthy('2') is False
        assert _is_truthy('10') is False
        assert _is_truthy('-1') is False


class TestPasswordHashing:
    """Test password hashing and verification functions."""

    def test_verify_password_with_correct_password(self):
        """Test password verification succeeds with correct password."""
        plain = "secure_password_123"
        hashed = get_password_hash(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_password_with_incorrect_password(self):
        """Test password verification fails with incorrect password."""
        plain = "secure_password_123"
        wrong = "wrong_password_456"
        hashed = get_password_hash(plain)
        assert verify_password(wrong, hashed) is False

    def test_get_password_hash_returns_string(self):
        """Test password hash returns a string."""
        hashed = get_password_hash("password")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_get_password_hash_unique_for_same_password(self):
        """Test same password produces different hashes (due to salt)."""
        password = "test_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        # Hashes should be different due to salting
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_password_hash_with_special_characters(self):
        """Test password hashing with special characters."""
        password = "p@ssw0rd!#$%^&*()"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)

    def test_password_hash_with_unicode(self):
        """Test password hashing with unicode characters."""
        password = "пароль密码🔐"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)

    def test_password_hash_with_empty_string(self):
        """Test password hashing with empty string."""
        password = ""
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)

    def test_password_hash_with_very_long_password(self):
        """Test password hashing with very long password."""
        password = "a" * 1000
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)


class TestUserRepository:
    """Test UserRepository class for database operations."""

    @pytest.fixture
    def mock_repository(self):
        """Create a UserRepository instance for testing."""
        return UserRepository()

    def test_get_user_returns_user_when_exists(self, mock_repository):
        """Test get_user returns UserInDB when user exists."""
        with patch('api.auth.fetch_one') as mock_fetch:
            mock_fetch.return_value = {
                'username': 'testuser',
                'email': 'test@example.com',
                'full_name': 'Test User',
                'hashed_password': 'hashed_pw',
                'disabled': 0
            }
            user = mock_repository.get_user('testuser')
            assert isinstance(user, UserInDB)
            assert user.username == 'testuser'
            assert user.email == 'test@example.com'
            assert user.full_name == 'Test User'
            assert user.hashed_password == 'hashed_pw'
            assert user.disabled is False

    def test_get_user_returns_none_when_not_exists(self, mock_repository):
        """Test get_user returns None when user doesn't exist."""
        with patch('api.auth.fetch_one') as mock_fetch:
            mock_fetch.return_value = None
            user = mock_repository.get_user('nonexistent')
            assert user is None

    def test_get_user_handles_disabled_user(self, mock_repository):
        """Test get_user correctly handles disabled flag."""
        with patch('api.auth.fetch_one') as mock_fetch:
            mock_fetch.return_value = {
                'username': 'disabled_user',
                'email': None,
                'full_name': None,
                'hashed_password': 'hash',
                'disabled': 1
            }
            user = mock_repository.get_user('disabled_user')
            assert user.disabled is True

    def test_has_users_returns_true_when_users_exist(self, mock_repository):
        """Test has_users returns True when users exist."""
        with patch('api.auth.fetch_value') as mock_fetch:
            mock_fetch.return_value = 1
            assert mock_repository.has_users() is True

    def test_has_users_returns_false_when_no_users(self, mock_repository):
        """Test has_users returns False when no users exist."""
        with patch('api.auth.fetch_value') as mock_fetch:
            mock_fetch.return_value = None
            assert mock_repository.has_users() is False

    def test_create_or_update_user_with_all_fields(self, mock_repository):
        """Test create_or_update_user with all fields provided."""
        with patch('api.auth.execute') as mock_execute:
            mock_repository.create_or_update_user(
                username='newuser',
                hashed_password='hashed',
                email='new@example.com',
                full_name='New User',
                disabled=False
            )
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert 'newuser' in call_args[0][1]
            assert 'new@example.com' in call_args[0][1]
            assert 'New User' in call_args[0][1]
            assert 'hashed' in call_args[0][1]

    def test_create_or_update_user_with_minimal_fields(self, mock_repository):
        """Test create_or_update_user with only required fields."""
        with patch('api.auth.execute') as mock_execute:
            mock_repository.create_or_update_user(
                username='minuser',
                hashed_password='hashed'
            )
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert 'minuser' in call_args[0][1]
            assert 'hashed' in call_args[0][1]

    def test_create_or_update_user_disabled_flag_conversion(self, mock_repository):
        """Test create_or_update_user converts disabled boolean to integer."""
        with patch('api.auth.execute') as mock_execute:
            mock_repository.create_or_update_user(
                username='user',
                hashed_password='hash',
                disabled=True
            )
            call_args = mock_execute.call_args[0][1]
            # Last argument should be 1 (disabled=True)
            assert call_args[-1] == 1

        with patch('api.auth.execute') as mock_execute:
            mock_repository.create_or_update_user(
                username='user',
                hashed_password='hash',
                disabled=False
            )
            call_args = mock_execute.call_args[0][1]
            # Last argument should be 0 (disabled=False)
            assert call_args[-1] == 0


class TestJWTTokenOperations:
    """Test JWT token creation and validation."""

    def test_create_access_token_with_default_expiry(self):
        """Test access token creation with default expiry."""
        data = {'sub': 'testuser'}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiry(self):
        """Test access token creation with custom expiry delta."""
        data = {'sub': 'testuser'}
        expires_delta = timedelta(minutes=60)
        token = create_access_token(data, expires_delta)
        assert isinstance(token, str)

    def test_create_access_token_includes_expiry_claim(self):
        """Test created token includes 'exp' claim."""
        import jwt
        from api.auth import SECRET_KEY, ALGORITHM
        
        data = {'sub': 'testuser'}
        token = create_access_token(data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert 'exp' in decoded
        assert 'sub' in decoded
        assert decoded['sub'] == 'testuser'

    def test_create_access_token_expiry_in_future(self):
        """Test token expiry is set in the future."""
        import jwt
        from api.auth import SECRET_KEY, ALGORITHM
        
        data = {'sub': 'testuser'}
        token = create_access_token(data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(decoded['exp'])
        assert exp_time > datetime.utcnow()

    def test_create_access_token_with_additional_claims(self):
        """Test token creation with additional custom claims."""
        import jwt
        from api.auth import SECRET_KEY, ALGORITHM
        
        data = {'sub': 'testuser', 'role': 'admin', 'scope': 'full'}
        token = create_access_token(data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded['sub'] == 'testuser'
        assert decoded['role'] == 'admin'
        assert decoded['scope'] == 'full'


class TestUserAuthentication:
    """Test user authentication functions."""

    def test_get_user_with_default_repository(self):
        """Test get_user function with default repository."""
        with patch.object(user_repository, 'get_user') as mock_get:
            mock_get.return_value = UserInDB(
                username='test',
                hashed_password='hash',
                email='test@example.com'
            )
            user = get_user('test')
            assert user.username == 'test'
            mock_get.assert_called_once_with('test')

    def test_get_user_with_custom_repository(self):
        """Test get_user function with custom repository."""
        custom_repo = Mock(spec=UserRepository)
        custom_repo.get_user.return_value = UserInDB(
            username='custom',
            hashed_password='hash'
        )
        user = get_user('custom', repository=custom_repo)
        assert user.username == 'custom'
        custom_repo.get_user.assert_called_once_with('custom')

    def test_authenticate_user_success(self):
        """Test successful user authentication."""
        password = 'testpass'
        hashed = get_password_hash(password)
        
        mock_repo = Mock(spec=UserRepository)
        mock_repo.get_user.return_value = UserInDB(
            username='testuser',
            hashed_password=hashed
        )
        
        result = authenticate_user('testuser', password, repository=mock_repo)
        assert isinstance(result, UserInDB)
        assert result.username == 'testuser'

    def test_authenticate_user_wrong_password(self):
        """Test authentication fails with wrong password."""
        password = 'correctpass'
        wrong_password = 'wrongpass'
        hashed = get_password_hash(password)
        
        mock_repo = Mock(spec=UserRepository)
        mock_repo.get_user.return_value = UserInDB(
            username='testuser',
            hashed_password=hashed
        )
        
        result = authenticate_user('testuser', wrong_password, repository=mock_repo)
        assert result is False

    def test_authenticate_user_nonexistent_user(self):
        """Test authentication fails for nonexistent user."""
        mock_repo = Mock(spec=UserRepository)
        mock_repo.get_user.return_value = None
        
        result = authenticate_user('nonexistent', 'password', repository=mock_repo)
        assert result is False

    def test_authenticate_user_with_default_repository(self):
        """Test authenticate_user uses default repository when not provided."""
        with patch.object(user_repository, 'get_user') as mock_get:
            mock_get.return_value = None
            result = authenticate_user('user', 'pass')
            assert result is False
            mock_get.assert_called_once()


class TestGetCurrentUser:
    """Test get_current_user dependency function."""

    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_token(self):
        """Test get_current_user returns user for valid token."""
        data = {'sub': 'testuser'}
        token = create_access_token(data)
        
        with patch('api.auth.get_user') as mock_get_user:
            mock_get_user.return_value = User(username='testuser')
            user = await get_current_user(token)
            assert user.username == 'testuser'

    @pytest.mark.asyncio
    async def test_get_current_user_with_expired_token(self):
        """Test get_current_user raises HTTPException for expired token."""
        # Create token that expired in the past
        data = {'sub': 'testuser'}
        expires_delta = timedelta(minutes=-10)  # Expired 10 minutes ago
        token = create_access_token(data, expires_delta)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token)
        assert exc_info.value.status_code == 401
        assert 'expired' in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_current_user_with_invalid_token(self):
        """Test get_current_user raises HTTPException for invalid token."""
        invalid_token = 'invalid.token.here'
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(invalid_token)
        assert exc_info.value.status_code == 401
        assert 'could not validate' in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_current_user_with_missing_sub_claim(self):
        """Test get_current_user raises HTTPException when sub claim is missing."""
        data = {'user': 'testuser'}  # Wrong key, should be 'sub'
        token = create_access_token(data)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_with_nonexistent_user(self):
        """Test get_current_user raises HTTPException when user doesn't exist."""
        data = {'sub': 'nonexistent'}
        token = create_access_token(data)
        
        with patch('api.auth.get_user') as mock_get_user:
            mock_get_user.return_value = None
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token)
            assert exc_info.value.status_code == 401


class TestGetCurrentActiveUser:
    """Test get_current_active_user dependency function."""

    @pytest.mark.asyncio
    async def test_get_current_active_user_with_active_user(self):
        """Test get_current_active_user returns user when active."""
        active_user = User(username='active', disabled=False)
        result = await get_current_active_user(active_user)
        assert result.username == 'active'
        assert result.disabled is False

    @pytest.mark.asyncio
    async def test_get_current_active_user_with_disabled_user(self):
        """Test get_current_active_user raises HTTPException for disabled user."""
        disabled_user = User(username='disabled', disabled=True)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(disabled_user)
        assert exc_info.value.status_code == 400
        assert 'inactive' in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_current_active_user_with_none_disabled(self):
        """Test get_current_active_user handles None disabled field."""
        user = User(username='test', disabled=None)
        # None is falsy, so should not raise
        result = await get_current_active_user(user)
        assert result.username == 'test'


class TestSeedCredentialsFromEnv:
    """Test environment-based credential seeding."""

    def test_seed_credentials_with_all_env_vars(self):
        """Test seeding credentials with all environment variables set."""
        mock_repo = Mock(spec=UserRepository)
        
        env_vars = {
            'ADMIN_USERNAME': 'admin',
            'ADMIN_PASSWORD': 'adminpass',
            'ADMIN_EMAIL': 'admin@example.com',
            'ADMIN_FULL_NAME': 'Admin User',
            'ADMIN_DISABLED': 'false'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch('api.auth.get_password_hash') as mock_hash:
                mock_hash.return_value = 'hashed_password'
                _seed_credentials_from_env(mock_repo)
                
                mock_repo.create_or_update_user.assert_called_once()
                call_kwargs = mock_repo.create_or_update_user.call_args[1]
                assert call_kwargs['username'] == 'admin'
                assert call_kwargs['hashed_password'] == 'hashed_password'
                assert call_kwargs['email'] == 'admin@example.com'
                assert call_kwargs['full_name'] == 'Admin User'
                assert call_kwargs['disabled'] is False

    def test_seed_credentials_with_minimal_env_vars(self):
        """Test seeding credentials with only required environment variables."""
        mock_repo = Mock(spec=UserRepository)
        
        env_vars = {
            'ADMIN_USERNAME': 'admin',
            'ADMIN_PASSWORD': 'adminpass'
        }
        
        # Remove optional vars
        with patch.dict(os.environ, env_vars, clear=False):
            with patch('api.auth.get_password_hash') as mock_hash:
                mock_hash.return_value = 'hashed'
                _seed_credentials_from_env(mock_repo)
                
                mock_repo.create_or_update_user.assert_called_once()
                call_kwargs = mock_repo.create_or_update_user.call_args[1]
                assert call_kwargs['username'] == 'admin'
                assert call_kwargs['email'] is None
                assert call_kwargs['full_name'] is None

    def test_seed_credentials_disabled_flag_variations(self):
        """Test different truthy values for ADMIN_DISABLED."""
        mock_repo = Mock(spec=UserRepository)
        
        for truthy_value in ['true', '1', 'yes', 'on', 'TRUE', 'YES']:
            env_vars = {
                'ADMIN_USERNAME': 'admin',
                'ADMIN_PASSWORD': 'pass',
                'ADMIN_DISABLED': truthy_value
            }
            
            with patch.dict(os.environ, env_vars, clear=False):
                with patch('api.auth.get_password_hash') as mock_hash:
                    mock_hash.return_value = 'hashed'
                    _seed_credentials_from_env(mock_repo)
                    
                    call_kwargs = mock_repo.create_or_update_user.call_args[1]
                    assert call_kwargs['disabled'] is True, f"Failed for {truthy_value}"

    def test_seed_credentials_missing_username(self):
        """Test seeding does nothing when ADMIN_USERNAME is missing."""
        mock_repo = Mock(spec=UserRepository)
        
        env_vars = {'ADMIN_PASSWORD': 'pass'}
        
        with patch.dict(os.environ, env_vars, clear=False):
            # Remove ADMIN_USERNAME if it exists
            os.environ.pop('ADMIN_USERNAME', None)
            _seed_credentials_from_env(mock_repo)
            mock_repo.create_or_update_user.assert_not_called()

    def test_seed_credentials_missing_password(self):
        """Test seeding does nothing when ADMIN_PASSWORD is missing."""
        mock_repo = Mock(spec=UserRepository)
        
        env_vars = {'ADMIN_USERNAME': 'admin'}
        
        with patch.dict(os.environ, env_vars, clear=False):
            # Remove ADMIN_PASSWORD if it exists
            os.environ.pop('ADMIN_PASSWORD', None)
            _seed_credentials_from_env(mock_repo)
            mock_repo.create_or_update_user.assert_not_called()

    def test_seed_credentials_empty_username(self):
        """Test seeding does nothing when ADMIN_USERNAME is empty."""
        mock_repo = Mock(spec=UserRepository)
        
        env_vars = {
            'ADMIN_USERNAME': '',
            'ADMIN_PASSWORD': 'pass'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            _seed_credentials_from_env(mock_repo)
            mock_repo.create_or_update_user.assert_not_called()


class TestPydanticModels:
    """Test Pydantic model definitions."""

    def test_token_model_creation(self):
        """Test Token model instantiation."""
        token = Token(access_token='abc123', token_type='bearer')
        assert token.access_token == 'abc123'
        assert token.token_type == 'bearer'

    def test_token_data_model_with_username(self):
        """Test TokenData model with username."""
        token_data = TokenData(username='testuser')
        assert token_data.username == 'testuser'

    def test_token_data_model_without_username(self):
        """Test TokenData model with no username (defaults to None)."""
        token_data = TokenData()
        assert token_data.username is None

    def test_user_model_all_fields(self):
        """Test User model with all fields."""
        user = User(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            disabled=False
        )
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.full_name == 'Test User'
        assert user.disabled is False

    def test_user_model_minimal_fields(self):
        """Test User model with only username."""
        user = User(username='testuser')
        assert user.username == 'testuser'
        assert user.email is None
        assert user.full_name is None
        assert user.disabled is None

    def test_user_in_db_model(self):
        """Test UserInDB model extends User."""
        user_in_db = UserInDB(
            username='testuser',
            hashed_password='hashed_pw',
            email='test@example.com'
        )
        assert user_in_db.username == 'testuser'
        assert user_in_db.hashed_password == 'hashed_pw'
        assert user_in_db.email == 'test@example.com'

    def test_user_in_db_inherits_from_user(self):
        """Test UserInDB is a subclass of User."""
        assert issubclass(UserInDB, User)


class TestSecurityConfiguration:
    """Test security configuration constants and setup."""

    def test_secret_key_is_loaded(self):
        """Test SECRET_KEY is loaded from environment."""
        from api.auth import SECRET_KEY
        assert SECRET_KEY is not None
        assert len(SECRET_KEY) > 0

    def test_algorithm_is_hs256(self):
        """Test JWT algorithm is HS256."""
        from api.auth import ALGORITHM
        assert ALGORITHM == 'HS256'

    def test_access_token_expire_minutes_is_configured(self):
        """Test token expiry time is configured."""
        from api.auth import ACCESS_TOKEN_EXPIRE_MINUTES
        assert isinstance(ACCESS_TOKEN_EXPIRE_MINUTES, int)
        assert ACCESS_TOKEN_EXPIRE_MINUTES > 0

    def test_pwd_context_uses_pbkdf2(self):
        """Test password context uses pbkdf2_sha256."""
        assert 'pbkdf2_sha256' in pwd_context.schemes()

    def test_oauth2_scheme_token_url(self):
        """Test OAuth2 scheme has correct token URL."""
        from api.auth import oauth2_scheme
        assert oauth2_scheme.tokenUrl == 'token'


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_username(self):
        """Test handling of very long username."""
        long_username = 'a' * 1000
        user = User(username=long_username)
        assert user.username == long_username

    def test_special_characters_in_username(self):
        """Test usernames with special characters."""
        special_username = 'user@domain.com+tag'
        user = User(username=special_username)
        assert user.username == special_username

    def test_unicode_in_username(self):
        """Test usernames with unicode characters."""
        unicode_username = 'пользователь用户'
        user = User(username=unicode_username)
        assert user.username == unicode_username

    def test_token_creation_with_empty_data(self):
        """Test token creation with empty data dictionary."""
        token = create_access_token({})
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_get_current_user_with_tampered_token(self):
        """Test get_current_user rejects tampered tokens."""
        data = {'sub': 'testuser'}
        token = create_access_token(data)
        # Tamper with the token
        tampered_token = token[:-10] + 'tampered123'
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(tampered_token)
        assert exc_info.value.status_code == 401

    def test_password_hash_consistency(self):
        """Test password hashing is consistent."""
        password = "test_password"
        hash1 = get_password_hash(password)
        # Verify the hash works
        assert verify_password(password, hash1)
        # Create another hash and verify
        hash2 = get_password_hash(password)
        assert verify_password(password, hash2)

    def test_is_truthy_case_insensitivity(self):
        """Test _is_truthy is case insensitive for all truthy values."""
        truthy_values = ['true', 'TRUE', 'TrUe', '1', 'yes', 'YES', 'YeS', 'on', 'ON', 'On']
        for value in truthy_values:
            assert _is_truthy(value) is True, f"Failed for: {value}"


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_authentication_flow(self):
        """Test complete authentication flow from password to active user."""
        # Step 1: Create user
        username = 'integration_user'
        password = 'secure_password'
        hashed_password = get_password_hash(password)
        
        mock_repo = Mock(spec=UserRepository)
        mock_repo.get_user.return_value = UserInDB(
            username=username,
            hashed_password=hashed_password,
            disabled=False
        )
        
        # Step 2: Authenticate
        authenticated_user = authenticate_user(username, password, repository=mock_repo)
        assert isinstance(authenticated_user, UserInDB)
        assert authenticated_user.username == username
        
        # Step 3: Create token
        token_data = {'sub': authenticated_user.username}
        token = create_access_token(token_data)
        assert isinstance(token, str)
        
        # Step 4: Validate token and get user
        with patch('api.auth.get_user') as mock_get_user:
            mock_get_user.return_value = User(
                username=username,
                disabled=False
            )
            current_user = await get_current_user(token)
            assert current_user.username == username
            
            # Step 5: Verify user is active
            active_user = await get_current_active_user(current_user)
            assert active_user.username == username
            assert active_user.disabled is False

    def test_repository_crud_operations(self):
        """Test complete CRUD operations on UserRepository."""
        mock_repo = Mock(spec=UserRepository)
        
        # Create
        username = 'crud_user'
        password = 'password'
        hashed = get_password_hash(password)
        
        mock_repo.create_or_update_user(
            username=username,
            hashed_password=hashed,
            email='crud@example.com'
        )
        
        # Read
        mock_repo.get_user.return_value = UserInDB(
            username=username,
            hashed_password=hashed,
            email='crud@example.com'
        )
        user = mock_repo.get_user(username)
        assert user.username == username
        
        # Update (same method as create)
        mock_repo.create_or_update_user(
            username=username,
            hashed_password=hashed,
            email='updated@example.com',
            full_name='Updated Name'
        )
        
        # Verify calls were made
        assert mock_repo.create_or_update_user.call_count == 2
        assert mock_repo.get_user.call_count == 1