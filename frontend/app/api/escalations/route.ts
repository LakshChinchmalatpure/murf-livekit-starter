import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';

const PYTHON_SCRIPT = path.join(process.cwd(), '..', 'backend', 'src', 'query_escalations.py');

function runPython(args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    // Escape arguments for the shell
    const cmd = `python "${PYTHON_SCRIPT}" ${args.map(arg => `"${arg}"`).join(' ')}`;
    exec(cmd, (error, stdout, stderr) => {
      if (error) {
        reject(error || stderr);
      } else {
        resolve(stdout);
      }
    });
  });
}

export const revalidate = 0;

export async function GET() {
  try {
    const output = await runPython(['list']);
    const data = JSON.parse(output);
    if (data.error) {
      return NextResponse.json({ error: data.error }, { status: 500 });
    }
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('Failed to query escalations:', error);
    return NextResponse.json({ error: error.message || error }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const { referenceId, status } = await req.json();
    if (!referenceId || !status) {
      return NextResponse.json({ error: 'Missing referenceId or status' }, { status: 400 });
    }
    const output = await runPython(['update', referenceId, status]);
    const data = JSON.parse(output);
    if (data.error) {
      return NextResponse.json({ error: data.error }, { status: 500 });
    }
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('Failed to update escalation:', error);
    return NextResponse.json({ error: error.message || error }, { status: 500 });
  }
}
