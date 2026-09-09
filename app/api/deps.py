"""Shared FastAPI dependencies: DB session, current user, role gating."""
import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.providers.imd_provider import IMDProvider
from app.providers.nasa_ocean_color_provider import NASAOceanColorProvider
from app.providers.noaa_coops_provider import NOAACoOpsProvider
from app.providers.noaa_ndbc_provider import NOAANDBCProvider
from app.providers.noaa_weather_provider import NOAAWeatherProvider
from app.providers.open_meteo_provider import OpenMeteoMarineProvider
from app.providers.tidesatlas_provider import TidesAtlasProvider

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_imd_provider(request: Request) -> IMDProvider:
    """Builds an IMDProvider using the app-lifetime shared httpx client."""
    return IMDProvider(client=request.app.state.http_client)


def get_open_meteo_provider(request: Request) -> OpenMeteoMarineProvider:
    """Builds an OpenMeteoMarineProvider using the app-lifetime shared httpx client."""
    return OpenMeteoMarineProvider(client=request.app.state.http_client)


def get_nasa_ocean_color_provider(request: Request) -> NASAOceanColorProvider:
    """Builds a NASAOceanColorProvider using the app-lifetime shared httpx client."""
    return NASAOceanColorProvider(client=request.app.state.http_client)


def get_noaa_coops_provider(request: Request) -> NOAACoOpsProvider:
    """Builds a NOAACoOpsProvider using the app-lifetime shared httpx client."""
    return NOAACoOpsProvider(client=request.app.state.http_client)


def get_noaa_ndbc_provider(request: Request) -> NOAANDBCProvider:
    """Builds a NOAANDBCProvider using the app-lifetime shared httpx client."""
    return NOAANDBCProvider(client=request.app.state.http_client)


def get_noaa_weather_provider(request: Request) -> NOAAWeatherProvider:
    """Builds a NOAAWeatherProvider using the app-lifetime shared httpx client."""
    return NOAAWeatherProvider(client=request.app.state.http_client)


def get_tidesatlas_provider(request: Request) -> TidesAtlasProvider:
    """Builds a TidesAtlasProvider using the app-lifetime shared httpx client."""
    return TidesAtlasProvider(client=request.app.state.http_client)


def get_marine_service(
    open_meteo: OpenMeteoMarineProvider = Depends(get_open_meteo_provider),
    imd: IMDProvider = Depends(get_imd_provider),
    nasa_ocean_color: NASAOceanColorProvider = Depends(get_nasa_ocean_color_provider),
    noaa_coops: NOAACoOpsProvider = Depends(get_noaa_coops_provider),
    noaa_ndbc: NOAANDBCProvider = Depends(get_noaa_ndbc_provider),
    noaa_weather: NOAAWeatherProvider = Depends(get_noaa_weather_provider),
    tidesatlas: TidesAtlasProvider = Depends(get_tidesatlas_provider),
):
    from app.services.marine_service import MarineDataService

    return MarineDataService(
        open_meteo=open_meteo,
        imd=imd,
        nasa_ocean_color=nasa_ocean_color,
        noaa_coops=noaa_coops,
        noaa_ndbc=noaa_ndbc,
        noaa_weather=noaa_weather,
        tidesatlas=tidesatlas,
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_error

    try:
        user_id = uuid.UUID(payload.sub)
    except ValueError:
        raise credentials_error

    user = db.get(User, user_id)
    if user is None:
        raise credentials_error
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def require_roles(*allowed_roles: UserRole):
    """Dependency factory: use as Depends(require_roles(UserRole.ADMIN))."""

    def _check(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return _check
