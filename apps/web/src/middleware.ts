import { NextRequest, NextResponse } from 'next/server';

function denied(){return new NextResponse('Staging access required.',{status:401,headers:{'WWW-Authenticate':'Basic realm="GhostWaste staging", charset="UTF-8"','Cache-Control':'no-store'}})}
export function middleware(request:NextRequest){
  if(request.nextUrl.pathname === '/healthz' && request.method === 'GET')
    return NextResponse.next();
  if(process.env.STAGING_AUTH_REQUIRED!=='true')return NextResponse.next();
  const user=process.env.STAGING_AUTH_USER||'',password=process.env.STAGING_AUTH_PASSWORD||'';
  if(!user||!password)return new NextResponse('Staging authentication is misconfigured.',{status:503,headers:{'Cache-Control':'no-store'}});
  const supplied=request.headers.get('authorization');
  if(!supplied?.startsWith('Basic '))return denied();
  try { const [u,p]=atob(supplied.slice(6)).split(':');if(u===user&&p===password)return NextResponse.next(); } catch { /* malformed credentials are rejected */ }
  return denied();
}
export const config={matcher:['/((?!_next/static|_next/image|favicon.ico).*)']};
