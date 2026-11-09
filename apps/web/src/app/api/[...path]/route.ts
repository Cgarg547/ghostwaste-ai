import { NextRequest, NextResponse } from 'next/server';

export const dynamic='force-dynamic';
const permitted=['content-type','accept'];

async function proxy(request:NextRequest,{params}:{params:Promise<{path:string[]}>}) {
  const {path}=await params;
  const origin=(process.env.BACKEND_ORIGIN||'http://127.0.0.1:8000').replace(/\/$/,'');
  const internalToken=process.env.API_INTERNAL_TOKEN||process.env.GHOSTWASTE_API_TOKEN||'';
  let target:URL;
  try { target=new URL(`${origin}/${path.map(encodeURIComponent).join('/')}${request.nextUrl.search}`); }
  catch { return NextResponse.json({detail:'API proxy is not configured.'},{status:503}); }
  const headers=new Headers();
  for(const key of permitted){const value=request.headers.get(key);if(value)headers.set(key,value)}
  if(internalToken)headers.set('authorization',`Bearer ${internalToken}`);
  const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),20_000);
  try {
    const response=await fetch(target,{method:request.method,headers,body:['GET','HEAD'].includes(request.method)?undefined:await request.arrayBuffer(),cache:'no-store',signal:controller.signal});
    const outgoing=new Headers();const contentType=response.headers.get('content-type');if(contentType)outgoing.set('content-type',contentType);
    return new NextResponse(response.body,{status:response.status,headers:outgoing});
  } catch { return NextResponse.json({detail:'The planning API is temporarily unavailable.'},{status:503}); }
  finally { clearTimeout(timeout); }
}
export const GET=proxy; export const POST=proxy; export const PUT=proxy; export const PATCH=proxy; export const DELETE=proxy;
